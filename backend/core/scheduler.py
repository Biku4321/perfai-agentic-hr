"""
Proactive Agent Scheduler
Uses APScheduler to trigger agents automatically:
- Daily cycle health checks
- Manager nudges (T-10, T-5, T-2 days before deadline)
- Bias scan on cycle start
- Auto-draft generation for pending reviews
"""
import os
from datetime import datetime, timedelta

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

_scheduler = None


def _run_daily_cycle_health_check():
    """Triggered daily: analyze cycle health and flag risks."""
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from agents.orchestrator import analyze_cycle_health, predict_completion_risk
        
        health = analyze_cycle_health()
        risks = predict_completion_risk()
        
        print(f"[{datetime.now().isoformat()}] Daily health check:")
        print(f"  Completion: {health['completion_rate']}% | At-risk managers: {len(risks)}")
        
        # Auto-nudge high-risk managers
        for risk in risks:
            if risk["risk_score"] > 60:
                _send_auto_nudge(risk["manager_id"])
    except Exception as e:
        print(f"[SCHEDULER] Health check error: {e}")


def _send_auto_nudge(manager_id: str):
    """Auto-send nudge to high-risk manager."""
    try:
        from core.effihr_db import get_current_cycle, get_all_employees
        from agents.manager_agent import generate_manager_nudge
        
        cycle = get_current_cycle()
        employees = get_all_employees()
        emp_map = {e["id"]: e for e in employees}
        
        pending = [
            r for r in cycle.get("reviews", [])
            if r["manager_id"] == manager_id and r["status"] in ("pending",)
        ]
        for r in pending:
            r["employee_name"] = emp_map.get(r["employee_id"], {}).get("name", r["employee_id"])
        
        if pending:
            result = generate_manager_nudge(manager_id, pending)
            print(f"[SCHEDULER] Auto-nudge sent to {manager_id}: {result['message'][:60]}...")
    except Exception as e:
        print(f"[SCHEDULER] Nudge error for {manager_id}: {e}")


def _run_bias_scan():
    """Weekly: run full bias scan and log any new flags."""
    try:
        from agents.orchestrator import detect_bias_patterns
        flags = detect_bias_patterns()
        print(f"[{datetime.now().isoformat()}] Weekly bias scan: {len(flags)} flags detected")
    except Exception as e:
        print(f"[SCHEDULER] Bias scan error: {e}")


def _auto_generate_pending_drafts():
    """Triggered T-3 days: auto-generate drafts for still-pending reviews."""
    try:
        from core.effihr_db import get_current_cycle
        from agents.manager_agent import generate_review_draft
        
        cycle = get_current_cycle()
        pending = [r for r in cycle.get("reviews", []) if r["status"] == "pending"]
        
        for review in pending:
            try:
                generate_review_draft(review["employee_id"], cycle["id"])
                print(f"[SCHEDULER] Auto-draft generated for {review['employee_id']}")
            except Exception as e:
                print(f"[SCHEDULER] Draft gen failed for {review['employee_id']}: {e}")
    except Exception as e:
        print(f"[SCHEDULER] Auto-draft generation error: {e}")


def init_scheduler():
    """
    Initialize and start the background scheduler.
    Call this from FastAPI startup event.
    """
    global _scheduler
    
    if not SCHEDULER_AVAILABLE:
        print("⚠️  APScheduler not available — proactive scheduling disabled")
        return None
    
    if _scheduler and _scheduler.running:
        return _scheduler
    
    _scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    
    # Daily health check at 9 AM IST
    _scheduler.add_job(
        _run_daily_cycle_health_check,
        CronTrigger(hour=9, minute=0),
        id="daily_health_check",
        replace_existing=True,
        name="Daily Cycle Health Check"
    )
    
    # Weekly bias scan every Monday at 10 AM IST
    _scheduler.add_job(
        _run_bias_scan,
        CronTrigger(day_of_week="mon", hour=10, minute=0),
        id="weekly_bias_scan",
        replace_existing=True,
        name="Weekly Bias Scan"
    )
    
    # Auto-generate pending drafts — runs every day at 8 PM IST
    _scheduler.add_job(
        _auto_generate_pending_drafts,
        CronTrigger(hour=20, minute=0),
        id="auto_draft_generation",
        replace_existing=True,
        name="Auto Draft Generation"
    )
    
    _scheduler.start()
    print("✅ PerfAI proactive scheduler started")
    print("   → Daily health checks: 9 AM IST")
    print("   → Weekly bias scans: Monday 10 AM IST")
    print("   → Auto-draft generation: 8 PM IST")
    
    return _scheduler


def shutdown_scheduler():
    """Gracefully shutdown the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        print("⏹️  Scheduler stopped")


def get_scheduler_status() -> dict:
    """Return current scheduler job statuses."""
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None
        })
    
    return {"running": True, "jobs": jobs}