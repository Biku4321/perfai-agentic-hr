"""
Vector Store — ChromaDB-based RAG layer
Stores employee work signal summaries as embeddings for semantic retrieval.
Used by agents to fetch relevant context when generating reviews or analysis.
"""
import json
from pathlib import Path
from typing import Optional


try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

SEED_PATH = Path(__file__).parent.parent / "data" / "seed_data.json"
DB_DIR = Path(__file__).parent.parent / "data" / "chroma_db"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if not CHROMA_AVAILABLE:
        return None
    if _collection is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(DB_DIR))
        ef = embedding_functions.DefaultEmbeddingFunction()
        _collection = _client.get_or_create_collection(
            name="employee_signals",
            embedding_function=ef
        )
    return _collection


def index_employee_signals():
    """
    Index all employee work signals into the vector store.
    Called on startup or when data is refreshed.
    """
    collection = _get_collection()
    if collection is None:
        print("⚠️  ChromaDB not available — skipping vector indexing")
        return False

    with open(SEED_PATH) as f:
        seed = json.load(f)

    employees = seed["employees"]
    signals = seed["work_signals"]
    goals = seed["goals"]

    documents = []
    metadatas = []
    ids = []

    for emp in employees:
        eid = emp["id"]

        # Gather all signals for this employee
        jira = next((e for e in signals.get("jira", []) if e["employee_id"] == eid), {})
        github = next((e for e in signals.get("github", []) if e["employee_id"] == eid), {})
        confluence = next((e for e in signals.get("confluence", []) if e["employee_id"] == eid), {})
        slack = next((e for e in signals.get("slack", []) if e["employee_id"] == eid), {})
        emp_goals = [g for g in goals if g["employee_id"] == eid]

        # Build natural language document for embedding
        goal_text = "; ".join([f"{g['title']} ({g['progress']}%)" for g in emp_goals])
        doc = f"""
Employee: {emp['name']} | Role: {emp['role']} | Department: {emp['department']} | Team: {emp['team']}
Goals: {goal_text if goal_text else 'None'}
Jira: {jira.get('tickets_closed', 0)} tickets closed, {jira.get('bugs_fixed', 0)} bugs fixed, {jira.get('sprint_velocity', 0)} velocity, {jira.get('on_time_delivery_pct', 0)}% on time
GitHub: {github.get('prs_merged', 0)} PRs merged, {github.get('prs_reviewed', 0)} PRs reviewed, {github.get('review_comments', 0)} review comments, {github.get('avg_review_turnaround_hrs', 0)}h avg turnaround
Confluence: {confluence.get('docs_authored', 0)} docs authored, {confluence.get('docs_updated', 0)} updated, {confluence.get('pages_viewed_by_others', 0)} views
Slack: {slack.get('messages_in_help_channels', 0)} help messages, {slack.get('responses_to_others', 0)} responses to teammates
        """.strip()

        documents.append(doc)
        metadatas.append({
            "employee_id": eid,
            "name": emp["name"],
            "role": emp["role"],
            "department": emp["department"],
            "manager_id": emp["manager_id"]
        })
        ids.append(f"emp_{eid}")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Indexed {len(documents)} employee profiles into vector store")
    return True


def search_similar_profiles(query: str, n_results: int = 3) -> list:
    """
    Semantic search over employee profiles.
    Useful for: 'find employees similar to Priya in terms of contribution'
    """
    collection = _get_collection()
    if collection is None:
        return []

    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        return [
            {
                "employee_id": m["employee_id"],
                "name": m["name"],
                "role": m["role"],
                "department": m["department"],
                "distance": d
            }
            for m, d in zip(results["metadatas"][0], results["distances"][0])
        ]
    except Exception as e:
        print(f"Vector search error: {e}")
        return []


def get_employee_vector_context(employee_id: str) -> Optional[str]:
    """
    Retrieve the stored vector document for an employee (for RAG injection).
    """
    collection = _get_collection()
    if collection is None:
        return None

    try:
        result = collection.get(ids=[f"emp_{employee_id}"])
        docs = result.get("documents", [])
        return docs[0] if docs else None
    except Exception:
        return None


def is_available() -> bool:
    return CHROMA_AVAILABLE