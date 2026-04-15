"""
GitHub Connector
Fetches PR, commit, and code review data for employees.
In production: uses GitHub REST API v3 / GraphQL with personal access tokens.
For hackathon: returns realistic mock data based on seed_data signals.
"""
import json
from pathlib import Path

SEED_PATH = Path(__file__).parent.parent / "data" / "seed_data.json"

def _load_seed() -> dict:
    with open(SEED_PATH) as f:
        return json.load(f)

def get_employee_github_signals(employee_id: str) -> dict:
    """
    Fetch GitHub contribution signals for an employee.
    Production: GET /repos/{owner}/{repo}/pulls?state=closed + GraphQL contributions
    """
    seed = _load_seed()
    for entry in seed["work_signals"].get("github", []):
        if entry["employee_id"] == employee_id:
            pr_review_ratio = round(
                entry.get("prs_reviewed", 0) / max(entry.get("prs_merged", 1), 1), 2
            )
            return {
                "source": "github",
                "employee_id": employee_id,
                "prs_merged": entry.get("prs_merged", 0),
                "prs_reviewed": entry.get("prs_reviewed", 0),
                "lines_added": entry.get("lines_added", 0),
                "lines_deleted": entry.get("lines_deleted", 0),
                "review_comments": entry.get("review_comments", 0),
                "avg_review_turnaround_hrs": entry.get("avg_review_turnaround_hrs", 0),
                "pr_review_ratio": pr_review_ratio,  # >1.5 = strong reviewer
                "net_lines": entry.get("lines_added", 0) - entry.get("lines_deleted", 0),
                "raw_available": True
            }
    return {"source": "github", "employee_id": employee_id, "raw_available": False}

def get_repo_contribution_summary(org: str = "effiHR-org") -> dict:
    """
    Org-level contribution summary.
    Production: GET /orgs/{org}/members + /repos/{repo}/stats/contributors
    """
    seed = _load_seed()
    all_github = seed["work_signals"].get("github", [])
    return {
        "source": "github",
        "org": org,
        "total_prs_merged": sum(e.get("prs_merged", 0) for e in all_github),
        "total_prs_reviewed": sum(e.get("prs_reviewed", 0) for e in all_github),
        "total_review_comments": sum(e.get("review_comments", 0) for e in all_github),
        "contributors_tracked": len(all_github)
    }

def detect_review_mentorship(employee_id: str) -> dict:
    """
    Detect if an employee is disproportionately doing code review work
    (invisible mentorship contribution).
    """
    signals = get_employee_github_signals(employee_id)
    if not signals.get("raw_available"):
        return {"is_reviewer_mentor": False}
    
    prs_reviewed = signals.get("prs_reviewed", 0)
    prs_authored = signals.get("prs_merged", 0)
    review_comments = signals.get("review_comments", 0)
    turnaround = signals.get("avg_review_turnaround_hrs", 99)
    
    is_mentor = prs_reviewed > 40 and prs_reviewed > prs_authored * 1.5
    fast_reviewer = turnaround < 8
    
    return {
        "employee_id": employee_id,
        "is_reviewer_mentor": is_mentor,
        "fast_reviewer": fast_reviewer,
        "review_to_author_ratio": round(prs_reviewed / max(prs_authored, 1), 2),
        "insight": (
            f"Reviews {prs_reviewed} PRs with avg {turnaround}hr turnaround — "
            f"significant team enablement contribution"
            if is_mentor else "Standard contribution pattern"
        )
    }