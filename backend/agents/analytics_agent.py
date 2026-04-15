"""
HR Analytics Agent
Tracks fairness, completion rates, rating trends, and generates
executive-level reports for HR leadership.
"""
import os
import json
import statistics
import google.generativeai as genai
from core.effihr_db import (
    get_all_employees, get_current_cycle, get_work_signals,
    get_bias_flags, get_nudge_log
)
from core.bias_detector import run_full_bias_scan


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def compute_completion_metrics() -> dict:
    """
    Compute detailed completion rate metrics by manager and department.
    """
    cycle = get_current_cycle()
    reviews = cycle.get("reviews", [])
    employees = get_all_employees()
    emp_map = {e["id"]: e for e in employees}

    # By status
    status_counts = {}
    for r in reviews:
        s = r["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    # By manager
    mgr_completion = {}
    for r in reviews:
        mid = r["manager_id"]
        if mid not in mgr_completion:
            mgr_completion[mid] = {"total": 0, "completed": 0, "pending": 0, "draft": 0}
        mgr_completion[mid]["total"] += 1
        if r["status"] == "completed":
            mgr_completion[mid]["completed"] += 1
        elif r["status"] == "pending":
            mgr_completion[mid]["pending"] += 1
        elif r["status"] == "draft_generated":
            mgr_completion[mid]["draft"] += 1

    # By department
    dept_completion = {}
    for r in reviews:
        emp = emp_map.get(r["employee_id"], {})
        dept = emp.get("department", "Unknown")
        if dept not in dept_completion:
            dept_completion[dept] = {"total": 0, "completed": 0}
        dept_completion[dept]["total"] += 1
        if r["status"] == "completed":
            dept_completion[dept]["completed"] += 1

    total = len(reviews)
    completed = status_counts.get("completed", 0)
    draft = status_counts.get("draft_generated", 0)
    pending = status_counts.get("pending", 0)

    return {
        "cycle_id": cycle["id"],
        "overall_completion_rate": round(completed / total * 100 if total > 0 else 0, 1),
        "ai_draft_rate": round((completed + draft) / total * 100 if total > 0 else 0, 1),
        "pending_rate": round(pending / total * 100 if total > 0 else 0, 1),
        "by_status": status_counts,
        "by_manager": mgr_completion,
        "by_department": dept_completion,
        "total_reviews": total
    }


def compute_rating_trends() -> dict:
    """
    Analyze historical rating trends across employees and departments.
    """
    employees = get_all_employees()

    dept_ratings = {}
    all_ratings = []
    individual_trends = []

    for emp in employees:
        past = emp.get("past_ratings", [])
        if not past:
            continue

        ratings = [r["rating"] for r in past]
        all_ratings.extend(ratings)

        # Trend direction (improving/declining/stable)
        if len(ratings) >= 2:
            trend = "improving" if ratings[-1] > ratings[0] else (
                "declining" if ratings[-1] < ratings[0] else "stable"
            )
        else:
            trend = "insufficient_data"

        individual_trends.append({
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "department": emp["department"],
            "avg_rating": round(sum(ratings) / len(ratings), 2),
            "latest_rating": ratings[-1],
            "trend": trend,
            "cycles": len(ratings)
        })

        dept = emp["department"]
        if dept not in dept_ratings:
            dept_ratings[dept] = []
        dept_ratings[dept].extend(ratings)

    dept_averages = {
        dept: round(statistics.mean(ratings), 2)
        for dept, ratings in dept_ratings.items()
        if ratings
    }

    org_avg = round(statistics.mean(all_ratings), 2) if all_ratings else 0

    return {
        "org_avg_rating": org_avg,
        "dept_averages": dept_averages,
        "individual_trends": individual_trends,
        "improving_employees": [t for t in individual_trends if t["trend"] == "improving"],
        "declining_employees": [t for t in individual_trends if t["trend"] == "declining"],
        "top_performers": sorted(
            [t for t in individual_trends if t["avg_rating"] >= 4.5],
            key=lambda x: x["avg_rating"],
            reverse=True
        )
    }


def predict_review_quality_scores() -> list:
    """
    Predict the quality of reviews based on data availability
    and manager engagement. Flags low-quality risk early.
    """
    cycle = get_current_cycle()
    reviews = cycle.get("reviews", [])
    employees = get_all_employees()
    emp_map = {e["id"]: e for e in employees}

    quality_scores = []
    for r in reviews:
        emp = emp_map.get(r["employee_id"], {})
        signals = get_work_signals(r["employee_id"])
        sources = [k for k, v in signals.items() if v]

        # Score: 0-100
        score = 0
        reasons = []

        # Data coverage (max 40 pts)
        score += len(sources) * 10
        if len(sources) >= 3:
            reasons.append(f"Good data coverage ({len(sources)} sources)")

        # AI draft generated (20 pts)
        if r["status"] == "draft_generated":
            score += 20
            reasons.append("AI draft generated")
        elif r["status"] == "completed":
            score += 30
            reasons.append("Review completed")

        # Historical data available (10 pts)
        past = emp.get("past_ratings", [])
        if past:
            score += 10
            reasons.append("Historical rating context available")

        # Goals tracked (10 pts)
        from core.effihr_db import get_employee_goals
        goals = get_employee_goals(r["employee_id"])
        if goals:
            score += 10
            reasons.append(f"{len(goals)} goals tracked")

        quality_scores.append({
            "employee_id": r["employee_id"],
            "employee_name": emp.get("name", ""),
            "manager_id": r["manager_id"],
            "status": r["status"],
            "quality_score": min(score, 100),
            "quality_band": "high" if score >= 70 else ("medium" if score >= 40 else "low"),
            "reasons": reasons,
            "data_sources": sources
        })

    return sorted(quality_scores, key=lambda x: x["quality_score"])


def generate_fairness_report() -> dict:
    """
    Comprehensive fairness report combining all bias signals,
    completion metrics, and rating trends.
    """
    employees = get_all_employees()
    cycle = get_current_cycle()
    reviews = cycle.get("reviews", [])

    bias_results = run_full_bias_scan(
        employees, reviews, get_work_signals
    )

    completion = compute_completion_metrics()
    trends = compute_rating_trends()
    quality = predict_review_quality_scores()

    low_quality = [q for q in quality if q["quality_band"] == "low"]

    prompt = f"""You are an HR analytics expert. Summarize this performance cycle fairness report in 150 words for the CHRO.

Completion: {completion['overall_completion_rate']}% done, {completion['pending_rate']}% still pending
AI-assisted: {completion['ai_draft_rate']}% of reviews have AI drafts
Bias flags: {bias_results['total_flags']} total ({bias_results['high_severity']} high, {bias_results['medium_severity']} medium severity)
Invisible contributors detected: {len([f for f in bias_results['flags'] if f['type'] == 'invisible_contributor'])}
High performer risks: {len([f for f in bias_results['flags'] if f['type'] == 'high_performer_neglect'])}
Low quality reviews at risk: {len(low_quality)}
Org avg rating: {trends['org_avg_rating']}/5.0
Improving employees: {len(trends['improving_employees'])} | Declining: {len(trends['declining_employees'])}

Format: 3 bullet points — Status, Key Risks, Immediate Actions. Be direct."""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=300)
    )

    return {
        "completion_metrics": completion,
        "rating_trends": trends,
        "bias_analysis": bias_results,
        "quality_scores": quality,
        "low_quality_at_risk": low_quality,
        "ai_executive_summary": response.text, 
        "nudges_sent": len(get_nudge_log()),
        "historical_bias_flags": get_bias_flags()
    }


def get_manager_effectiveness_report(manager_id: str) -> dict:
    """
    Report on a specific manager's review quality and team rating patterns.
    """
    cycle = get_current_cycle()
    manager_reviews = [r for r in cycle.get("reviews", []) if r["manager_id"] == manager_id]
    employees = get_all_employees()
    emp_map = {e["id"]: e for e in employees}

    team_ratings = []
    for r in manager_reviews:
        emp = emp_map.get(r["employee_id"], {})
        past = emp.get("past_ratings", [])
        if past:
            avg = sum(p["rating"] for p in past) / len(past)
            team_ratings.append({"name": emp.get("name"), "avg": avg})

    pending_count = sum(1 for r in manager_reviews if r["status"] == "pending")
    drafted_count = sum(1 for r in manager_reviews if r["status"] == "draft_generated")
    completed_count = sum(1 for r in manager_reviews if r["status"] == "completed")

    return {
        "manager_id": manager_id,
        "total_direct_reports": len(manager_reviews),
        "completed": completed_count,
        "drafted": drafted_count,
        "pending": pending_count,
        "completion_rate": round(completed_count / len(manager_reviews) * 100 if manager_reviews else 0, 1),
        "team_avg_rating": round(
            sum(t["avg"] for t in team_ratings) / len(team_ratings)
            if team_ratings else 0, 2
        ),
        "team_ratings": team_ratings
    }