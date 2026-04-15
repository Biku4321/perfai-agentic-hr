import json
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "effihr.db"
SEED_PATH = Path(__file__).parent.parent / "data" / "seed_data.json"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with open(SEED_PATH) as f:
        seed = json.load(f)

    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY, name TEXT, role TEXT, department TEXT,
            manager_id TEXT, team TEXT, hire_date TEXT, past_ratings TEXT
        );
        CREATE TABLE IF NOT EXISTS managers (
            id TEXT PRIMARY KEY, name TEXT, role TEXT, department TEXT
        );
        CREATE TABLE IF NOT EXISTS goals (
            id TEXT PRIMARY KEY, employee_id TEXT, title TEXT,
            progress INTEGER, cycle TEXT, due_date TEXT
        );
        CREATE TABLE IF NOT EXISTS appraisal_cycles (
            id TEXT PRIMARY KEY, name TEXT, start_date TEXT,
            deadline TEXT, status TEXT, completion_rate INTEGER
        );
        CREATE TABLE IF NOT EXISTS reviews (
            employee_id TEXT, manager_id TEXT, cycle_id TEXT,
            status TEXT, days_overdue INTEGER, final_rating REAL,
            ai_draft TEXT, PRIMARY KEY (employee_id, cycle_id)
        );
        CREATE TABLE IF NOT EXISTS attendance (
            employee_id TEXT PRIMARY KEY, present_days INTEGER,
            total_days INTEGER, late_arrivals INTEGER
        );
        CREATE TABLE IF NOT EXISTS work_signals (
            employee_id TEXT PRIMARY KEY, signals_json TEXT
        );
        CREATE TABLE IF NOT EXISTS nudge_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id TEXT, target_type TEXT, message TEXT,
            channel TEXT, sent_at TEXT, agent TEXT
        );
        CREATE TABLE IF NOT EXISTS bias_flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_id TEXT, flag_type TEXT, description TEXT,
            severity TEXT, detected_at TEXT, resolved INTEGER DEFAULT 0
        );
    """)

    for emp in seed["employees"]:
        c.execute("INSERT OR REPLACE INTO employees VALUES (?,?,?,?,?,?,?,?)",
                  (emp["id"], emp["name"], emp["role"], emp["department"],
                   emp["manager_id"], emp["team"], emp["hire_date"],
                   json.dumps(emp["past_ratings"])))

    for mgr in seed["managers"]:
        c.execute("INSERT OR REPLACE INTO managers VALUES (?,?,?,?)",
                  (mgr["id"], mgr["name"], mgr["role"], mgr["department"]))

    for g in seed["goals"]:
        c.execute("INSERT OR REPLACE INTO goals VALUES (?,?,?,?,?,?)",
                  (g["id"], g["employee_id"], g["title"], g["progress"], g["cycle"], g["due_date"]))

    cyc = seed["appraisal_cycle"]
    c.execute("INSERT OR REPLACE INTO appraisal_cycles VALUES (?,?,?,?,?,?)",
              (cyc["id"], cyc["name"], cyc["start_date"], cyc["deadline"],
               cyc["status"], cyc["completion_rate"]))

    for r in cyc["reviews"]:
        c.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?,?,?,?,?)",
                  (r["employee_id"], r["manager_id"], cyc["id"], r["status"],
                   r.get("days_overdue", 0), r.get("final_rating"), None))

    for att in seed["attendance"]:
        c.execute("INSERT OR REPLACE INTO attendance VALUES (?,?,?,?)",
                  (att["employee_id"], att["present_days"], att["total_days"], att["late_arrivals"]))

    # Merge all work signals per employee
    signals = seed["work_signals"]
    all_emp_ids = {e["id"] for e in seed["employees"]}
    for eid in all_emp_ids:
        merged = {}
        for source in ["jira", "github", "confluence", "slack"]:
            for entry in signals.get(source, []):
                if entry["employee_id"] == eid:
                    merged[source] = {k: v for k, v in entry.items() if k != "employee_id"}
        c.execute("INSERT OR REPLACE INTO work_signals VALUES (?,?)",
                  (eid, json.dumps(merged)))

    conn.commit()
    conn.close()
    print("✅ effiHR database initialized")


def get_employee(employee_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["past_ratings"] = json.loads(d["past_ratings"])
    return d


def get_all_employees() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM employees").fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["past_ratings"] = json.loads(d["past_ratings"])
        result.append(d)
    return result


def get_employee_goals(employee_id: str) -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM goals WHERE employee_id=?", (employee_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_work_signals(employee_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT signals_json FROM work_signals WHERE employee_id=?", (employee_id,)).fetchone()
    conn.close()
    return json.loads(row["signals_json"]) if row else {}


def get_current_cycle() -> dict:
    conn = get_connection()
    cycle = conn.execute("SELECT * FROM appraisal_cycles ORDER BY start_date DESC LIMIT 1").fetchone()
    reviews = conn.execute("SELECT * FROM reviews WHERE cycle_id=?", (cycle["id"],)).fetchall()
    conn.close()
    return {**dict(cycle), "reviews": [dict(r) for r in reviews]}


def update_review_draft(employee_id: str, cycle_id: str, draft: str):
    conn = get_connection()
    conn.execute("UPDATE reviews SET ai_draft=?, status='draft_generated' WHERE employee_id=? AND cycle_id=?",
                 (draft, employee_id, cycle_id))
    conn.commit()
    conn.close()


def get_review(employee_id: str, cycle_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM reviews WHERE employee_id=? AND cycle_id=?",
                       (employee_id, cycle_id)).fetchone()
    conn.close()
    return dict(row) if row else None


def log_nudge(target_id: str, target_type: str, message: str, channel: str, agent: str):
    from datetime import datetime
    conn = get_connection()
    conn.execute("INSERT INTO nudge_log (target_id, target_type, message, channel, sent_at, agent) VALUES (?,?,?,?,?,?)",
                 (target_id, target_type, message, channel, datetime.now().isoformat(), agent))
    conn.commit()
    conn.close()


def log_bias_flag(manager_id: str, flag_type: str, description: str, severity: str):
    from datetime import datetime
    conn = get_connection()
    conn.execute("INSERT INTO bias_flags (manager_id, flag_type, description, severity, detected_at) VALUES (?,?,?,?,?)",
                 (manager_id, flag_type, description, severity, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_bias_flags() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bias_flags WHERE resolved=0 ORDER BY detected_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_nudge_log() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM nudge_log ORDER BY sent_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_manager_team(manager_id: str) -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM employees WHERE manager_id=?", (manager_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance(employee_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM attendance WHERE employee_id=?", (employee_id,)).fetchone()
    conn.close()
    return dict(row) if row else None