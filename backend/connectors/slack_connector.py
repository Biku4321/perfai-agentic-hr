"""
Slack Connector
Fetches collaboration and help-channel signals for employees.
In production: uses Slack Web API with bot token scopes (channels:history, users:read).
For hackathon: returns realistic mock data from seed_data.
"""
import json
from pathlib import Path

SEED_PATH = Path(__file__).parent.parent / "data" / "seed_data.json"

def _load_seed() -> dict:
    with open(SEED_PATH) as f:
        return json.load(f)

def get_employee_slack_signals(employee_id: str) -> dict:
    """
    Fetch Slack collaboration signals.
    Production: conversations.history + users.info + reactions.list
    """
    seed = _load_seed()
    for entry in seed["work_signals"].get("slack", []):
        if entry["employee_id"] == employee_id:
            help_responses = entry.get("responses_to_others", 0)
            help_messages = entry.get("messages_in_help_channels", 0)
            
            # Compute helpfulness score
            helpfulness_score = round(
                (help_responses * 2 + help_messages) / 10, 1
            )
            
            return {
                "source": "slack",
                "employee_id": employee_id,
                "messages_in_help_channels": help_messages,
                "responses_to_others": help_responses,
                "threads_started": entry.get("threads_started", 0),
                "emoji_reactions_given": entry.get("emoji_reactions_given", 0),
                "helpfulness_score": helpfulness_score,
                "is_team_enabler": help_responses > 80 or helpfulness_score > 25,
                "raw_available": True
            }
    return {"source": "slack", "employee_id": employee_id, "raw_available": False}

def detect_team_enablers(employees: list) -> list:
    """
    Find employees who enable others via Slack help channels.
    These contributions often go unmeasured in traditional reviews.
    """
    enablers = []
    for emp in employees:
        signals = get_employee_slack_signals(emp["id"])
        if not signals.get("raw_available"):
            continue
        
        if signals.get("is_team_enabler"):
            enablers.append({
                "employee_id": emp["id"],
                "employee_name": emp.get("name", ""),
                "help_responses": signals["responses_to_others"],
                "help_messages": signals["messages_in_help_channels"],
                "helpfulness_score": signals["helpfulness_score"],
                "insight": (
                    f"Responded to {signals['responses_to_others']} teammate messages "
                    f"in help channels — strong team enabler pattern"
                )
            })
    return sorted(enablers, key=lambda x: x["helpfulness_score"], reverse=True)

def get_channel_activity_summary() -> dict:
    """
    Summary of help channel activity across the org.
    """
    seed = _load_seed()
    all_slack = seed["work_signals"].get("slack", [])
    return {
        "source": "slack",
        "total_help_messages": sum(e.get("messages_in_help_channels", 0) for e in all_slack),
        "total_responses": sum(e.get("responses_to_others", 0) for e in all_slack),
        "total_reactions": sum(e.get("emoji_reactions_given", 0) for e in all_slack),
        "contributors_tracked": len(all_slack)
    }

def send_slack_nudge(manager_id: str, message: str, webhook_url: str = None) -> dict:
    """
    Send a Slack nudge message to a manager.
    Production: POST to Slack Incoming Webhook or chat.postMessage API.
    For hackathon: simulates the send.
    """
    print(f"[SLACK NUDGE] → Manager {manager_id}: {message[:60]}...")
    return {
        "status": "simulated",
        "manager_id": manager_id,
        "channel": "#hr-reminders",
        "message_preview": message[:100],
        "note": "In production, sends via Slack Incoming Webhook"
    }