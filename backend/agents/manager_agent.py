"""
Manager Assistant Agent
- Generates evidence-based review drafts using real work signals
- Sends intelligent deadline nudges
- Flags bias patterns
"""

import os
import google.generativeai as genai
from core.effihr_db import (
    get_employee, get_employee_goals, get_work_signals,
    get_attendance, update_review_draft, log_nudge, get_manager_team
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def build_employee_context(employee_id: str) -> dict:
    employee = get_employee(employee_id)
    goals = get_employee_goals(employee_id)
    signals = get_work_signals(employee_id)
    attendance = get_attendance(employee_id)
    return {
        "employee": employee,
        "goals": goals,
        "work_signals": signals,
        "attendance": attendance
    }


def generate_review_draft(employee_id: str, cycle_id: str, manager_context: str = "") -> dict:
    """
    Generate an AI-powered, evidence-grounded performance review draft.
    """
    ctx = build_employee_context(employee_id)
    emp = ctx["employee"]
    goals = ctx["goals"]
    signals = ctx["work_signals"]
    att = ctx["attendance"]

    goal_summary = "\n".join([
        f"- {g['title']}: {g['progress']}% complete" for g in goals
    ])

    jira = signals.get("jira", {})
    github = signals.get("github", {})
    confluence = signals.get("confluence", {})
    slack = signals.get("slack", {})

    past_ratings = emp.get("past_ratings", [])
    avg_past = sum(r["rating"] for r in past_ratings) / len(past_ratings) if past_ratings else None

    prompt = f"""You are an expert performance review coach. Generate a fair, balanced, evidence-based performance review DRAFT for a manager to review and edit.

## Employee Profile
Name: {emp['name']}
Role: {emp['role']}
Department: {emp['department']}
Team: {emp['team']}
Tenure: Since {emp['hire_date']}
Historical avg rating: {avg_past if avg_past else 'First cycle'}

## Goals This Cycle
{goal_summary}

## Attendance
Present: {att['present_days']}/{att['total_days']} days ({round(att['present_days']/att['total_days']*100)}%)
Late arrivals: {att['late_arrivals']}

## Work Signals (Objective Data)
### Jira / Ticketing
{f"Tickets closed: {jira.get('tickets_closed', 'N/A')}" if jira else "No Jira data"}
{f"Bugs fixed: {jira.get('bugs_fixed', 'N/A')}" if jira else ""}
{f"Sprint velocity: {jira.get('sprint_velocity', 'N/A')} pts" if jira else ""}
{f"On-time delivery: {jira.get('on_time_delivery_pct', 'N/A')}%" if jira else ""}

### GitHub / Code
{f"PRs merged: {github.get('prs_merged', 'N/A')}" if github else "No GitHub data"}
{f"PRs reviewed for others: {github.get('prs_reviewed', 'N/A')}" if github else ""}
{f"Review comments given: {github.get('review_comments', 'N/A')}" if github else ""}
{f"Avg review turnaround: {github.get('avg_review_turnaround_hrs', 'N/A')} hrs" if github else ""}

### Knowledge & Documentation (Confluence)
{f"Docs authored: {confluence.get('docs_authored', 'N/A')}" if confluence else "No Confluence data"}
{f"Docs updated: {confluence.get('docs_updated', 'N/A')}" if confluence else ""}
{f"Views by others: {confluence.get('pages_viewed_by_others', 'N/A')}" if confluence else ""}

### Collaboration (Slack)
{f"Help channel messages: {slack.get('messages_in_help_channels', 'N/A')}" if slack else "No Slack data"}
{f"Responses to teammates: {slack.get('responses_to_others', 'N/A')}" if slack else ""}

{f"Manager additional context: {manager_context}" if manager_context else ""}

## Instructions
Generate a structured performance review draft with these sections:
1. **Executive Summary** (2-3 sentences, overall assessment)
2. **Key Achievements** (3-5 bullet points, ALWAYS cite specific data evidence)
3. **Goal Performance** (comment on each goal with context)
4. **Collaboration & Invisible Contributions** (flag any mentoring/documentation/knowledge sharing)
5. **Areas for Growth** (1-2 constructive, specific areas with actionable suggestions)
6. **Suggested Rating** (1-5 scale, with brief justification)
7. **Draft Summary for Employee** (2-3 sentences they'd see)

Be specific — cite numbers from the data. Avoid generic phrases like "team player" without evidence. Flag if any area lacks data to assess fairly.
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=1500)
    )

    draft_text = response.text 
    update_review_draft(employee_id, cycle_id, draft_text)

    return {
        "employee_id": employee_id,
        "employee_name": emp["name"],
        "cycle_id": cycle_id,
        "draft": draft_text,
        "evidence_sources": list(signals.keys()),
        "goals_count": len(goals)
    }


def generate_manager_nudge(manager_id: str, pending_reviews: list) -> dict:
    """
    Generate a personalized, intelligent nudge for a manager with pending reviews.
    """
    team = get_manager_team(manager_id)
    pending_names = [p.get("employee_name", p.get("employee_id")) for p in pending_reviews]

    prompt = f"""You are a helpful HR assistant. Write a SHORT, friendly, non-intrusive Slack message to a manager reminding them to complete {len(pending_reviews)} pending performance review(s).

Pending reviews for: {', '.join(pending_names)}
Days until deadline: 5

Guidelines:
- Be warm and helpful, not bureaucratic
- Mention that AI has pre-generated draft content to make it easy
- Keep it under 80 words
- Don't guilt-trip, offer help instead
- Include one specific benefit (e.g., "takes 15 min with the AI draft ready")
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=200)
    )

    message = response.text 
    log_nudge(manager_id, "manager", message, "slack", "manager_assistant_agent")

    return {
        "manager_id": manager_id,
        "message": message,
        "pending_count": len(pending_reviews),
        "channel": "slack"
    }


def generate_self_assessment_help(employee_id: str) -> dict:
    """
    Help an employee write their self-assessment using their own work data.
    """
    ctx = build_employee_context(employee_id)
    emp = ctx["employee"]
    goals = ctx["goals"]
    signals = ctx["work_signals"]

    goal_summary = "\n".join([f"- {g['title']}: {g['progress']}%" for g in goals])

    prompt = f"""You are a career coach helping {emp['name']}, a {emp['role']}, write their performance self-assessment.

Their goals this cycle:
{goal_summary}

Work signals available: {list(signals.keys())}

Generate 5 self-assessment talking points they could use, each:
1. Starting with a specific accomplishment (cite data where possible)
2. Explaining the business impact
3. Being written in first-person, confident but not boastful
4. Under 50 words each

Also suggest 1 honest area for growth they could mention proactively (shows self-awareness).
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=800)
    )

    return {
        "employee_id": employee_id,
        "employee_name": emp["name"],
        "talking_points": response.text
    }


def chat_with_agent(user_message: str, context: dict = None) -> str:
    """
    Conversational interface to the manager assistant agent.
    """
    system = """You are PerfAI, an intelligent performance management assistant embedded in effiHR. 
    You help managers write fair, evidence-based reviews, track team performance, and identify coaching opportunities.
    You have access to Jira, GitHub, Confluence, and Slack signals for every employee.
    Be concise, specific, and always ground recommendations in data.
    When you don't have data, say so clearly rather than guessing."""
    prompt_text = f"System Instructions:\n{system}\n\n"
    if context:
        prompt_text += f"Context: {context}\n\n"
    prompt_text += f"User Message:\n{user_message}"

    chat_model = genai.GenerativeModel("gemini-2.5-flash")
    response = chat_model.generate_content(
        prompt_text,
        generation_config={"max_output_tokens": 600}
    )
    return response.text