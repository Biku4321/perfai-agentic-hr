import os

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))



from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")



from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from core.scheduler import init_scheduler, shutdown_scheduler

from pydantic import BaseModel

from typing import Optional

import json



from core.effihr_db import (

    init_db, get_all_employees, get_employee, get_employee_goals,

    get_work_signals, get_current_cycle, get_review, get_nudge_log,

    get_bias_flags, get_manager_team, get_attendance

)

from agents.manager_agent import (

    generate_review_draft, generate_manager_nudge,

    generate_self_assessment_help, chat_with_agent

)

from agents.orchestrator import (

    analyze_cycle_health, detect_bias_patterns,

    generate_hr_summary_report, predict_completion_risk

)



app = FastAPI(title="PerfAI — Agentic Performance Layer", version="1.0.0")



app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "https://perfai-agentic-hr.vercel.app", 
        "http://localhost:3000"                 
    ],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],

)



# Initialize DB on startup

@app.on_event("startup")

async def startup():

    init_db()
    init_scheduler()
    print("✅ PerfAI backend ready")

@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()



# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/")

def root():

    return {"status": "PerfAI running", "version": "1.0.0"}





# ─── Employees ────────────────────────────────────────────────────────────────

@app.get("/api/employees")

def list_employees():

    return get_all_employees()





@app.get("/api/employees/{employee_id}")

def get_emp(employee_id: str):

    emp = get_employee(employee_id)

    if not emp:

        raise HTTPException(404, "Employee not found")

    goals = get_employee_goals(employee_id)

    signals = get_work_signals(employee_id)

    attendance = get_attendance(employee_id)

    return {**emp, "goals": goals, "work_signals": signals, "attendance": attendance}





@app.get("/api/employees/{employee_id}/signals")

def emp_signals(employee_id: str):

    return get_work_signals(employee_id)





# ─── Appraisal Cycle ──────────────────────────────────────────────────────────

@app.get("/api/cycle")

def current_cycle():

    return get_current_cycle()





@app.get("/api/cycle/health")

def cycle_health():

    return analyze_cycle_health()





@app.get("/api/cycle/risk")

def cycle_risk():

    return predict_completion_risk()





# ─── Review Drafts ────────────────────────────────────────────────────────────

class DraftRequest(BaseModel):

    employee_id: str

    cycle_id: str

    manager_context: Optional[str] = ""





@app.post("/api/reviews/generate-draft")

def generate_draft(req: DraftRequest):

    try:

        result = generate_review_draft(req.employee_id, req.cycle_id, req.manager_context)

        return result

    except Exception as e:

        raise HTTPException(500, str(e))





@app.get("/api/reviews/{employee_id}/{cycle_id}")

def get_review_endpoint(employee_id: str, cycle_id: str):

    review = get_review(employee_id, cycle_id)

    if not review:

        raise HTTPException(404, "Review not found")

    return review





# ─── Manager Endpoints ────────────────────────────────────────────────────────

@app.get("/api/managers/{manager_id}/team")

def manager_team(manager_id: str):

    team = get_manager_team(manager_id)

    cycle = get_current_cycle()

    reviews_map = {r["employee_id"]: r for r in cycle.get("reviews", [])}



    result = []

    for emp in team:

        d = dict(emp)

        d["past_ratings"] = json.loads(d["past_ratings"]) if isinstance(d["past_ratings"], str) else d["past_ratings"]

        d["review_status"] = reviews_map.get(emp["id"], {}).get("status", "not_started")

        d["has_ai_draft"] = reviews_map.get(emp["id"], {}).get("ai_draft") is not None

        signals = get_work_signals(emp["id"])

        d["signal_sources"] = list(signals.keys())

        result.append(d)

    return result





class NudgeRequest(BaseModel):

    manager_id: str





@app.post("/api/managers/nudge")

def send_nudge(req: NudgeRequest):

    cycle = get_current_cycle()

    pending = [r for r in cycle.get("reviews", [])

               if r["manager_id"] == req.manager_id and r["status"] == "pending"]

    if not pending:

        return {"message": "No pending reviews for this manager"}

    employees = get_all_employees()

    emp_map = {e["id"]: e for e in employees}

    for r in pending:

        r["employee_name"] = emp_map.get(r["employee_id"], {}).get("name", r["employee_id"])

    return generate_manager_nudge(req.manager_id, pending)





# ─── Employee Self-Assessment ─────────────────────────────────────────────────

@app.get("/api/employees/{employee_id}/self-assessment-help")

def self_assessment_help(employee_id: str):

    try:

        return generate_self_assessment_help(employee_id)

    except Exception as e:

        raise HTTPException(500, str(e))





# ─── HR Analytics & Orchestration ────────────────────────────────────────────

@app.get("/api/hr/dashboard")

def hr_dashboard():

    return generate_hr_summary_report()





@app.get("/api/hr/bias-flags")

def bias_flags():

    detected = detect_bias_patterns()

    db_flags = get_bias_flags()

    return {"detected": detected, "historical": db_flags}





@app.get("/api/hr/nudge-log")

def nudge_log_endpoint():

    return get_nudge_log()





# ─── Agent Chat ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):

    message: str

    context: Optional[dict] = None





@app.post("/api/chat")

def agent_chat(req: ChatRequest):

    try:

        response = chat_with_agent(req.message, req.context)

        return {"response": response}

    except Exception as e:

        raise HTTPException(500, str(e))





# ─── Batch Operations ─────────────────────────────────────────────────────────

@app.post("/api/agents/run-cycle-scan")

def run_cycle_scan():

    """

    Trigger the orchestration agent to scan the full cycle,

    generate missing drafts, send nudges, detect bias.

    """

    health = analyze_cycle_health()

    bias_flags_list = detect_bias_patterns()

    risks = predict_completion_risk()



    actions_taken = []



    # Auto-generate drafts for pending reviews

    cycle = get_current_cycle()

    for review in cycle.get("reviews", []):

        if review["status"] == "pending":

            try:

                generate_review_draft(review["employee_id"], cycle["id"])

                actions_taken.append(f"Generated draft for {review['employee_id']}")

            except Exception as e:

                actions_taken.append(f"Failed draft for {review['employee_id']}: {str(e)}")



    # Send nudges to at-risk managers

    for risk in risks:

        if risk["risk_score"] > 30:

            try:

                pending = [r for r in cycle.get("reviews", [])

                           if r["manager_id"] == risk["manager_id"] and r["status"] in ("pending", "draft_generated")]

                employees = get_all_employees()

                emp_map = {e["id"]: e for e in employees}

                for r in pending:

                    r["employee_name"] = emp_map.get(r["employee_id"], {}).get("name", r["employee_id"])

                generate_manager_nudge(risk["manager_id"], pending)

                actions_taken.append(f"Nudge sent to manager {risk['manager_id']}")

            except Exception as e:

                actions_taken.append(f"Nudge failed for {risk['manager_id']}: {str(e)}")



    return {

        "scan_complete": True,

        "health": health,

        "bias_flags_count": len(bias_flags_list),

        "at_risk_managers": len(risks),

        "actions_taken": actions_taken

    }