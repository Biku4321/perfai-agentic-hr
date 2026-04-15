"""
Employee Performance Coach Agent
Helps employees:
- Write compelling, evidence-based self-assessments
- Understand goal progress and gaps
- Prepare for performance conversations
- Get career growth recommendations
"""
import os
import google.generativeai as genai
from core.effihr_db import (
    get_employee, get_employee_goals, get_work_signals, get_attendance,
    get_current_cycle, get_review
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")


def generate_self_assessment_points(employee_id: str) -> dict:
    """
    Generate 5 evidence-based self-assessment talking points
    grounded in the employee's actual work signals.
    """
    emp = get_employee(employee_id)
    if not emp:
        return {"error": "Employee not found"}

    goals = get_employee_goals(employee_id)
    signals = get_work_signals(employee_id)
    att = get_attendance(employee_id)

    goal_text = "\n".join([f"- {g['title']}: {g['progress']}% complete" for g in goals])
    jira = signals.get("jira", {})
    github = signals.get("github", {})
    confluence = signals.get("confluence", {})
    slack = signals.get("slack", {})

    prompt = f"""You are a career coach helping {emp['name']} ({emp['role']}) write their performance self-assessment.

Their actual work data this cycle:
Goals:
{goal_text if goal_text else "No goals recorded"}

Jira: {jira.get('tickets_closed','N/A')} tickets closed, {jira.get('bugs_fixed','N/A')} bugs fixed, {jira.get('sprint_velocity','N/A')} velocity, {jira.get('on_time_delivery_pct','N/A')}% on-time
GitHub: {github.get('prs_merged','N/A')} PRs merged, {github.get('prs_reviewed','N/A')} reviewed, {github.get('review_comments','N/A')} review comments
Confluence: {confluence.get('docs_authored','N/A')} docs authored, {confluence.get('pages_viewed_by_others','N/A')} views
Slack: {slack.get('responses_to_others','N/A')} teammate responses, {slack.get('messages_in_help_channels','N/A')} help channel messages
Attendance: {att['present_days']}/{att['total_days']} days present

Generate exactly 5 self-assessment talking points. Each must:
1. Be written in first-person ("I delivered...", "I led...")
2. Cite specific numbers from the data above
3. Explain business impact (not just activity)
4. Be concise — max 60 words each
5. Be authentic and confident, not boastful

Then add:
- 1 "Growth Area" they could mention to show self-awareness
- 1 "Undervalued Contribution" they should specifically highlight that managers often miss

Format as JSON with keys: talking_points (array of 5 strings), growth_area (string), undervalued_contribution (string)"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=1000)
    )

    raw = response.text # FIXED
    # Try to parse JSON, fallback to raw text
    try:
        import json, re
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = {"raw": raw}
    except Exception:
        parsed = {"raw": raw}

    return {
        "employee_id": employee_id,
        "employee_name": emp["name"],
        "role": emp["role"],
        "assessment_content": parsed,
        "signals_used": list(signals.keys())
    }


def analyze_goal_gaps(employee_id: str) -> dict:
    """
    Analyze which goals are at risk and what the employee
    should prioritize before the cycle closes.
    """
    emp = get_employee(employee_id)
    goals = get_employee_goals(employee_id)
    signals = get_work_signals(employee_id)

    at_risk_goals = [g for g in goals if g["progress"] < 70]
    on_track_goals = [g for g in goals if g["progress"] >= 70]
    completed_goals = [g for g in goals if g["progress"] == 100]

    if not at_risk_goals:
        recommendation = "All goals on track. Focus on documenting impact for your self-assessment."
    else:
        titles = [g["title"] for g in at_risk_goals]
        recommendation = (
            f"Prioritize: {', '.join(titles[:2])}. "
            f"With {100 - max(g['progress'] for g in at_risk_goals)}% remaining, "
            f"focus on delivering a clear partial win you can articulate."
        )

    return {
        "employee_id": employee_id,
        "employee_name": emp["name"] if emp else employee_id,
        "total_goals": len(goals),
        "completed": len(completed_goals),
        "on_track": len(on_track_goals),
        "at_risk": len(at_risk_goals),
        "at_risk_goals": at_risk_goals,
        "on_track_goals": on_track_goals,
        "completed_goals": completed_goals,
        "overall_progress": round(
            sum(g["progress"] for g in goals) / len(goals) if goals else 0, 1
        ),
        "recommendation": recommendation
    }


def get_career_coaching_message(employee_id: str, employee_question: str) -> str:
    """
    Conversational career coaching — employee asks, agent responds
    using their actual data as context.
    """
    emp = get_employee(employee_id)
    goals = get_employee_goals(employee_id)
    signals = get_work_signals(employee_id)
    past_ratings = emp.get("past_ratings", []) if emp else []

    avg_rating = (
        sum(r["rating"] for r in past_ratings) / len(past_ratings)
        if past_ratings else None
    )

    system = f"""You are a supportive, data-driven performance coach for {emp['name'] if emp else 'the employee'}, 
a {emp['role'] if emp else 'team member'} at the company.

Their current cycle data:
- Goals completed: {sum(1 for g in goals if g['progress'] == 100)}/{len(goals)}
- Overall goal progress: {round(sum(g['progress'] for g in goals)/len(goals) if goals else 0, 1)}%
- Historical avg rating: {f'{avg_rating:.1f}/5.0' if avg_rating else 'First cycle'}
- Data sources available: {list(signals.keys())}

Be specific, encouraging, and ground all advice in their actual data.
Keep responses under 150 words. Be warm but direct."""

    coach_model = genai.GenerativeModel(
        "gemini-2.5-flash-lite", 
        system_instruction=system
    )
    
    response = coach_model.generate_content(
        employee_question,
        generation_config=genai.GenerationConfig(max_output_tokens=400)
    )
    return response.text # FIXED


def get_peer_comparison_insights(employee_id: str, department: str) -> dict:
    """
    Anonymized comparison of employee signals against dept averages.
    Helps employees understand where they stand without exposing others.
    """
    from core.effihr_db import get_all_employees
    all_emps = get_all_employees()
    dept_emps = [e for e in all_emps if e["department"] == department and e["id"] != employee_id]

    if not dept_emps:
        return {"message": "No comparison data available for your department"}

    emp_signals = get_work_signals(employee_id)
    emp_jira = emp_signals.get("jira", {})
    emp_github = emp_signals.get("github", {})

    dept_jira_velocities = []
    dept_prs = []
    for de in dept_emps:
        ds = get_work_signals(de["id"])
        if ds.get("jira", {}).get("sprint_velocity"):
            dept_jira_velocities.append(ds["jira"]["sprint_velocity"])
        if ds.get("github", {}).get("prs_merged"):
            dept_prs.append(ds["github"]["prs_merged"])

    avg_velocity = sum(dept_jira_velocities) / len(dept_jira_velocities) if dept_jira_velocities else 0
    avg_prs = sum(dept_prs) / len(dept_prs) if dept_prs else 0

    emp_velocity = emp_jira.get("sprint_velocity", 0)
    emp_prs = emp_github.get("prs_merged", 0)

    return {
        "employee_id": employee_id,
        "department": department,
        "velocity": {
            "yours": emp_velocity,
            "dept_avg": round(avg_velocity, 1),
            "position": "above average" if emp_velocity > avg_velocity else "below average"
        },
        "prs_merged": {
            "yours": emp_prs,
            "dept_avg": round(avg_prs, 1),
            "position": "above average" if emp_prs > avg_prs else "below average"
        },
        "note": "Anonymized — shows only department averages, not individual peer data"
    }