"""
HR Orchestration Agent — Supervisor
- Monitors appraisal cycle health
- Detects rating anomalies and bias patterns
- Identifies invisible contributors
- Predicts deadline risk
- Escalates issues to HR
"""

import os
import json
import google.generativeai as genai
from core.effihr_db import (
    get_current_cycle, get_all_employees, get_work_signals,
    get_bias_flags, log_bias_flag, get_nudge_log, get_manager_team
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")


def analyze_cycle_health() -> dict:
    """
    Analyze the current appraisal cycle and return health metrics.
    """
    cycle = get_current_cycle()
    reviews = cycle.get("reviews", [])

    total = len(reviews)
    completed = sum(1 for r in reviews if r["status"] == "completed")
    draft_generated = sum(1 for r in reviews if r["status"] == "draft_generated")
    pending = sum(1 for r in reviews if r["status"] == "pending")

    completion_rate = round((completed / total * 100) if total > 0 else 0)
    ai_assist_rate = round(((completed + draft_generated) / total * 100) if total > 0 else 0)

    risk_managers = []
    from collections import Counter
    mgr_status = {}
    for r in reviews:
        mid = r["manager_id"]
        if mid not in mgr_status:
            mgr_status[mid] = {"pending": 0, "done": 0}
        if r["status"] in ("pending",):
            mgr_status[mid]["pending"] += 1
        else:
            mgr_status[mid]["done"] += 1

    for mid, counts in mgr_status.items():
        if counts["pending"] > 0:
            risk_managers.append({
                "manager_id": mid,
                "pending_reviews": counts["pending"],
                "deadline_risk": "high" if counts["pending"] >= 2 else "medium"
            })

    return {
        "cycle_id": cycle["id"],
        "cycle_name": cycle["name"],
        "deadline": cycle["deadline"],
        "total_reviews": total,
        "completed": completed,
        "draft_generated": draft_generated,
        "pending": pending,
        "completion_rate": completion_rate,
        "ai_assist_rate": ai_assist_rate,
        "at_risk_managers": risk_managers,
        "status": cycle["status"]
    }


def detect_bias_patterns() -> list:
    """
    Statistical analysis to detect potential rating bias patterns.
    Returns list of bias flags with severity.
    """
    employees = get_all_employees()
    flags = []

    # Department-level: check if any dept consistently rated lower
    dept_signals = {}
    for emp in employees:
        dept = emp["department"]
        signals = get_work_signals(emp["id"])
        jira = signals.get("jira", {})
        github = signals.get("github", {})

        if dept not in dept_signals:
            dept_signals[dept] = {"velocities": [], "prs": [], "employees": []}

        if jira.get("sprint_velocity"):
            dept_signals[dept]["velocities"].append(jira["sprint_velocity"])
        if github.get("prs_merged"):
            dept_signals[dept]["prs"].append(github["prs_merged"])
        dept_signals[dept]["employees"].append(emp["name"])

    # Invisible contributor detection
    invisible_contributors = detect_invisible_contributors(employees)
    for ic in invisible_contributors:
        flags.append({
            "type": "invisible_contributor",
            "employee_id": ic["employee_id"],
            "employee_name": ic["employee_name"],
            "description": ic["description"],
            "severity": "medium",
            "recommendation": "Ensure review explicitly captures collaboration contributions"
        })

    # Check for historically high performers with no review started
    cycle = get_current_cycle()
    reviews_map = {r["employee_id"]: r for r in cycle.get("reviews", [])}
    for emp in employees:
        past = emp.get("past_ratings", [])
        if past:
            avg = sum(r["rating"] for r in past) / len(past)
            review = reviews_map.get(emp["id"], {})
            if avg >= 4.5 and review.get("status") == "pending":
                flags.append({
                    "type": "high_performer_review_risk",
                    "employee_id": emp["id"],
                    "employee_name": emp["name"],
                    "description": f"Historically rated {avg:.1f}/5.0 but review not yet started",
                    "severity": "medium",
                    "recommendation": "Prioritize review — high performers most affected by delayed/rushed feedback"
                })

    # Log new flags to DB
    for flag in flags:
        if flag["type"] in ("recency_bias", "high_performer_review_risk"):
            log_bias_flag(
                flag.get("manager_id", "system"),
                flag["type"],
                flag["description"],
                flag["severity"]
            )

    return flags


def detect_invisible_contributors(employees: list) -> list:
    """
    Find employees doing significant mentoring/collaboration work 
    that won't show up in tickets or PRs.
    """
    invisible = []
    for emp in employees:
        signals = get_work_signals(emp["id"])
        slack = signals.get("slack", {})
        confluence = signals.get("confluence", {})
        github = signals.get("github", {})

        # High PR review activity but not necessarily code author
        pr_reviews = github.get("prs_reviewed", 0)
        review_comments = github.get("review_comments", 0)
        pr_authored = github.get("prs_merged", 0)

        # High doc contribution
        docs_authored = confluence.get("docs_authored", 0)
        doc_views = confluence.get("pages_viewed_by_others", 0)

        # High help channel activity
        help_responses = slack.get("responses_to_others", 0)

        is_invisible = False
        reasons = []

        if pr_reviews > 40 and pr_authored < pr_reviews * 0.6:
            is_invisible = True
            reasons.append(f"Reviewed {pr_reviews} PRs for others (high code review mentorship)")

        if docs_authored >= 6 and doc_views > 200:
            is_invisible = True
            reasons.append(f"Authored {docs_authored} docs viewed {doc_views}+ times (knowledge multiplier)")

        if help_responses > 100:
            is_invisible = True
            reasons.append(f"Responded {help_responses}x in help channels (team enablement)")

        if is_invisible:
            invisible.append({
                "employee_id": emp["id"],
                "employee_name": emp["name"],
                "description": "Significant invisible contributions detected: " + "; ".join(reasons),
                "reasons": reasons
            })

    return invisible


def generate_hr_summary_report() -> dict:
    """
    Generate an executive summary of cycle health for HR.
    """
    health = analyze_cycle_health()
    flags = detect_bias_patterns()
    nudge_log = get_nudge_log()

    prompt = f"""You are an HR analytics expert. Generate a concise executive summary (max 200 words) for the HR team about the current performance appraisal cycle.

Cycle Health:
- Completion rate: {health['completion_rate']}%
- AI-assisted reviews: {health['ai_assist_rate']}%
- Pending: {health['pending']} reviews
- At-risk managers: {len(health['at_risk_managers'])}
- Nudges sent: {len(nudge_log)}

Bias/Fairness Flags:
{json.dumps(flags[:3], indent=2) if flags else "None detected"}

Write 3 short sections: Status, Risks, Recommended Actions.
Be direct and data-driven.
"""

    response = model.generate_content(
        prompt,
        generation_config={"max_output_tokens": 400} 
    )

    return {
        "health": health,
        "bias_flags": flags,
        "nudges_sent": len(nudge_log),
        "ai_summary": response.text, 
        "invisible_contributors": [f for f in flags if f["type"] == "invisible_contributor"]
    }

def predict_completion_risk() -> list:
    """
    Predict which managers are likely to miss the deadline.
    Returns ranked list with risk scores.
    """
    health = analyze_cycle_health()
    risks = []

    for mgr in health["at_risk_managers"]:
        risk_score = 0
        if mgr["pending_reviews"] >= 3:
            risk_score = 90
        elif mgr["pending_reviews"] == 2:
            risk_score = 65
        else:
            risk_score = 40

        risks.append({
            **mgr,
            "risk_score": risk_score,
            "recommendation": "Auto-generate AI drafts and send priority nudge" if risk_score > 60 else "Send friendly reminder"
        })

    return sorted(risks, key=lambda x: x["risk_score"], reverse=True)