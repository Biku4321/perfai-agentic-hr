"""
Bias Detector
Statistical and pattern-based bias detection for performance reviews.
Analyzes rating patterns, identifies invisible contributors,
and flags potential fairness issues before cycle closes.
"""
import json
import statistics
from pathlib import Path
from typing import Optional

SEED_PATH = Path(__file__).parent.parent / "data" / "seed_data.json"


def _load_seed() -> dict:
    with open(SEED_PATH) as f:
        return json.load(f)


def detect_recency_bias(reviews: list, employees: list) -> list:
    """
    Detect if managers started reviews late — correlates with recency bias
    (only remembering the last 4-6 weeks of performance).
    """
    flags = []
    late_starters = [r for r in reviews if r.get("status") == "pending" and r.get("days_overdue", 0) > 3]

    for review in late_starters:
        emp = next((e for e in employees if e["id"] == review["employee_id"]), None)
        if emp:
            flags.append({
                "type": "recency_bias_risk",
                "employee_id": emp["id"],
                "employee_name": emp.get("name", ""),
                "manager_id": review["manager_id"],
                "description": (
                    f"Review for {emp.get('name')} started late — "
                    f"manager may only recall recent performance. "
                    f"AI draft uses full 6-month signal data to counter this."
                ),
                "severity": "medium",
                "recommendation": "Use AI-generated draft anchored to full-cycle data"
            })
    return flags


def detect_dept_rating_disparity(employees: list) -> list:
    """
    Check if any department consistently scores lower than others
    despite similar work signal quality.
    """
    dept_ratings = {}
    for emp in employees:
        dept = emp.get("department", "Unknown")
        past = emp.get("past_ratings", [])
        if past:
            avg = sum(r["rating"] for r in past) / len(past)
            if dept not in dept_ratings:
                dept_ratings[dept] = []
            dept_ratings[dept].append(avg)

    flags = []
    if len(dept_ratings) < 2:
        return flags

    all_avgs = [avg for ratings in dept_ratings.values() for avg in ratings]
    if len(all_avgs) < 2:
        return flags
    
    global_mean = statistics.mean(all_avgs)
    global_stdev = statistics.stdev(all_avgs) if len(all_avgs) > 1 else 0.5

    for dept, ratings in dept_ratings.items():
        dept_mean = statistics.mean(ratings)
        if global_stdev > 0 and abs(dept_mean - global_mean) > global_stdev:
            direction = "lower" if dept_mean < global_mean else "higher"
            flags.append({
                "type": "dept_rating_disparity",
                "department": dept,
                "dept_avg_rating": round(dept_mean, 2),
                "global_avg_rating": round(global_mean, 2),
                "description": (
                    f"{dept} department rated {direction} than org average "
                    f"({dept_mean:.2f} vs {global_mean:.2f}) — "
                    f"verify this reflects actual performance vs structural bias"
                ),
                "severity": "low" if abs(dept_mean - global_mean) < 0.5 else "medium",
                "recommendation": "Cross-reference with objective work signal data"
            })
    return flags


def detect_high_performer_neglect(employees: list, reviews_map: dict) -> list:
    """
    High performers often get less attention during review cycles
    because managers assume they're 'fine'. Detect this pattern.
    """
    flags = []
    for emp in employees:
        past = emp.get("past_ratings", [])
        if not past:
            continue
        avg = sum(r["rating"] for r in past) / len(past)
        review = reviews_map.get(emp["id"], {})
        
        if avg >= 4.3 and review.get("status") == "pending":
            flags.append({
                "type": "high_performer_neglect",
                "employee_id": emp["id"],
                "employee_name": emp.get("name", ""),
                "manager_id": review.get("manager_id", ""),
                "historical_avg": round(avg, 2),
                "description": (
                    f"{emp.get('name')} has a {avg:.1f}/5.0 historical rating "
                    f"but their review hasn't been started. "
                    f"High performers are most sensitive to delayed, low-quality feedback."
                ),
                "severity": "medium",
                "recommendation": "Prioritize this review — high performers at flight risk without quality feedback"
            })
    return flags


def detect_invisible_contributors_bias(employees: list, signals_fn) -> list:
    """
    Identify employees whose real contributions (mentoring, documentation,
    code review) won't show up in basic metrics — creating structural bias.
    """
    flags = []
    for emp in employees:
        signals = signals_fn(emp["id"])
        github = signals.get("github", {})
        confluence = signals.get("confluence", {})
        slack = signals.get("slack", {})

        invisible_reasons = []

        # Code review mentorship (reviews >> authored)
        prs_reviewed = github.get("prs_reviewed", 0)
        prs_merged = github.get("prs_merged", 0)
        if prs_reviewed > 40 and prs_reviewed > prs_merged * 1.5:
            invisible_reasons.append(
                f"Reviewed {prs_reviewed} PRs (vs {prs_merged} authored) — "
                f"significant code review mentorship"
            )

        # Documentation knowledge multiplier
        docs = confluence.get("docs_authored", 0)
        views = confluence.get("pages_viewed_by_others", 0)
        if docs >= 6 and views > 200:
            invisible_reasons.append(
                f"Authored {docs} docs with {views} views — "
                f"knowledge base multiplier effect"
            )

        # Slack team enablement
        responses = slack.get("responses_to_others", 0)
        if responses > 80:
            invisible_reasons.append(
                f"Responded {responses}x in help channels — "
                f"reduces team blockers and onboarding friction"
            )

        if invisible_reasons:
            flags.append({
                "type": "invisible_contributor",
                "employee_id": emp["id"],
                "employee_name": emp.get("name", ""),
                "description": "Invisible contributions detected: " + " | ".join(invisible_reasons),
                "reasons": invisible_reasons,
                "severity": "medium",
                "recommendation": (
                    "Ensure review draft explicitly captures collaboration contributions. "
                    "These will NOT appear in ticket counts or PR merge numbers."
                )
            })
    return flags


def run_full_bias_scan(employees: list, reviews: list, signals_fn) -> dict:
    """
    Run all bias detection checks and return a comprehensive report.
    """
    reviews_map = {r["employee_id"]: r for r in reviews}

    recency_flags = detect_recency_bias(reviews, employees)
    dept_flags = detect_dept_rating_disparity(employees)
    neglect_flags = detect_high_performer_neglect(employees, reviews_map)
    invisible_flags = detect_invisible_contributors_bias(employees, signals_fn)

    all_flags = recency_flags + dept_flags + neglect_flags + invisible_flags

    high_severity = [f for f in all_flags if f.get("severity") == "high"]
    medium_severity = [f for f in all_flags if f.get("severity") == "medium"]
    low_severity = [f for f in all_flags if f.get("severity") == "low"]

    return {
        "total_flags": len(all_flags),
        "high_severity": len(high_severity),
        "medium_severity": len(medium_severity),
        "low_severity": len(low_severity),
        "flags": all_flags,
        "summary": (
            f"{len(all_flags)} fairness signals detected: "
            f"{len(invisible_flags)} invisible contributors, "
            f"{len(neglect_flags)} high-performer risks, "
            f"{len(recency_flags)} recency bias risks, "
            f"{len(dept_flags)} dept disparities"
        )
    }