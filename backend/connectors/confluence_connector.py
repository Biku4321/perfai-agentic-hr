"""
Confluence Connector
Fetches documentation, knowledge sharing signals for employees.
In production: uses Confluence REST API v2 with OAuth.
For hackathon: returns realistic mock data from seed_data.
"""
import json
from pathlib import Path

SEED_PATH = Path(__file__).parent.parent / "data" / "seed_data.json"

def _load_seed() -> dict:
    with open(SEED_PATH) as f:
        return json.load(f)

def get_employee_confluence_signals(employee_id: str) -> dict:
    """
    Fetch Confluence knowledge contribution signals.
    Production: GET /wiki/api/v2/pages?author={accountId}&sort=modified-date
    """
    seed = _load_seed()
    for entry in seed["work_signals"].get("confluence", []):
        if entry["employee_id"] == employee_id:
            docs_authored = entry.get("docs_authored", 0)
            doc_views = entry.get("pages_viewed_by_others", 0)
            
            # Compute knowledge multiplier: views per doc authored
            knowledge_multiplier = round(doc_views / max(docs_authored, 1), 1)
            
            return {
                "source": "confluence",
                "employee_id": employee_id,
                "docs_authored": docs_authored,
                "docs_updated": entry.get("docs_updated", 0),
                "pages_viewed_by_others": doc_views,
                "comments_received": entry.get("comments_received", 0),
                "knowledge_multiplier": knowledge_multiplier,
                "is_knowledge_leader": knowledge_multiplier > 30 or docs_authored >= 10,
                "raw_available": True
            }
    return {"source": "confluence", "employee_id": employee_id, "raw_available": False}

def get_space_contribution_summary(space_key: str = "EFFIHR") -> dict:
    """
    Space-level summary of contributions.
    Production: GET /wiki/api/v2/spaces/{spaceKey}/pages
    """
    seed = _load_seed()
    all_conf = seed["work_signals"].get("confluence", [])
    return {
        "source": "confluence",
        "space": space_key,
        "total_docs_authored": sum(e.get("docs_authored", 0) for e in all_conf),
        "total_docs_updated": sum(e.get("docs_updated", 0) for e in all_conf),
        "total_views": sum(e.get("pages_viewed_by_others", 0) for e in all_conf),
        "contributors_tracked": len(all_conf)
    }

def detect_knowledge_leaders(employees: list) -> list:
    """
    Identify employees who are significant knowledge contributors
    (invisible contribution pattern).
    """
    leaders = []
    for emp in employees:
        signals = get_employee_confluence_signals(emp["id"])
        if not signals.get("raw_available"):
            continue
        
        if signals.get("is_knowledge_leader"):
            leaders.append({
                "employee_id": emp["id"],
                "employee_name": emp.get("name", ""),
                "docs_authored": signals["docs_authored"],
                "views": signals["pages_viewed_by_others"],
                "knowledge_multiplier": signals["knowledge_multiplier"],
                "insight": (
                    f"Authored {signals['docs_authored']} docs with "
                    f"{signals['pages_viewed_by_others']} total views — "
                    f"significant knowledge base contributor"
                )
            })
    return sorted(leaders, key=lambda x: x["knowledge_multiplier"], reverse=True)