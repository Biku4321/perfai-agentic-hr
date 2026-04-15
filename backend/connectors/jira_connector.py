"""
Jira Connector
Fetches ticket/sprint data for employees.
In production: uses Jira REST API v3 with OAuth.
For hackathon: returns realistic mock data based on seed_data signals.
"""
import os
import json
from pathlib import Path

SEED_PATH = Path(__file__).parent.parent / "data" / "seed_data.json"

def _load_seed() -> dict:
    with open(SEED_PATH) as f:
        return json.load(f)

def get_employee_jira_signals(employee_id: str) -> dict:
    """
    Fetch Jira signals for an employee.
    Production: GET /rest/api/3/search?jql=assignee={accountId}&maxResults=100
    """
    seed = _load_seed()
    for entry in seed["work_signals"].get("jira", []):
        if entry["employee_id"] == employee_id:
            return {
                "source": "jira",
                "employee_id": employee_id,
                "tickets_closed": entry.get("tickets_closed", 0),
                "bugs_fixed": entry.get("bugs_fixed", 0),
                "stories_owned": entry.get("stories_owned", 0),
                "sprint_velocity": entry.get("sprint_velocity", 0),
                "critical_bugs": entry.get("critical_bugs", 0),
                "on_time_delivery_pct": entry.get("on_time_delivery_pct", 0),
                "raw_available": True
            }
    return {"source": "jira", "employee_id": employee_id, "raw_available": False}

def get_team_jira_velocity(manager_id: str, team_member_ids: list) -> dict:
    """
    Fetch aggregated team velocity from Jira.
    """
    seed = _load_seed()
    team_data = []
    for entry in seed["work_signals"].get("jira", []):
        if entry["employee_id"] in team_member_ids:
            team_data.append(entry)
    
    if not team_data:
        return {"source": "jira", "manager_id": manager_id, "team_velocity": 0}
    
    avg_velocity = sum(e.get("sprint_velocity", 0) for e in team_data) / len(team_data)
    total_tickets = sum(e.get("tickets_closed", 0) for e in team_data)
    avg_delivery = sum(e.get("on_time_delivery_pct", 0) for e in team_data) / len(team_data)
    
    return {
        "source": "jira",
        "manager_id": manager_id,
        "team_velocity_avg": round(avg_velocity, 1),
        "total_tickets_closed": total_tickets,
        "avg_on_time_delivery_pct": round(avg_delivery, 1),
        "members_tracked": len(team_data)
    }

def get_sprint_board_summary() -> dict:
    """
    Summary of all active sprints.
    Production: GET /rest/agile/1.0/board/{boardId}/sprint?state=active
    """
    seed = _load_seed()
    all_jira = seed["work_signals"].get("jira", [])
    return {
        "source": "jira",
        "active_sprint": "Sprint 24",
        "total_team_velocity": sum(e.get("sprint_velocity", 0) for e in all_jira),
        "total_tickets_in_progress": 12,
        "overdue_tickets": 3
    }