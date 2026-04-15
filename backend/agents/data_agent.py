"""
Data Aggregation Agent
Pulls and normalizes signals from all external systems:
Jira, GitHub, Confluence, Slack → unified employee performance profile.
Runs on schedule and on-demand before review generation.
"""
import os
import json
import google.generativeai as genai
from connectors.jira_connector import get_employee_jira_signals, get_team_jira_velocity
from connectors.github_connector import get_employee_github_signals, detect_review_mentorship
from connectors.confluence_connector import get_employee_confluence_signals
from connectors.slack_connector import get_employee_slack_signals, detect_team_enablers
from core.effihr_db import get_all_employees, get_work_signals

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")

def aggregate_employee_signals(employee_id: str) -> dict:
    """
    Pull signals from all sources and return a normalized profile.
    This is the single source of truth for an employee's work evidence.
    """
    jira = get_employee_jira_signals(employee_id)
    github = get_employee_github_signals(employee_id)
    confluence = get_employee_confluence_signals(employee_id)
    slack = get_employee_slack_signals(employee_id)

    # Also check DB signals (may have more recent data)
    db_signals = get_work_signals(employee_id)

    sources_available = []
    if jira.get("raw_available"):
        sources_available.append("jira")
    if github.get("raw_available"):
        sources_available.append("github")
    if confluence.get("raw_available"):
        sources_available.append("confluence")
    if slack.get("raw_available"):
        sources_available.append("slack")

    # Detect special patterns
    review_mentorship = detect_review_mentorship(employee_id)

    return {
        "employee_id": employee_id,
        "sources_available": sources_available,
        "jira": jira,
        "github": github,
        "confluence": confluence,
        "slack": slack,
        "patterns": {
            "is_reviewer_mentor": review_mentorship.get("is_reviewer_mentor", False),
            "reviewer_mentor_insight": review_mentorship.get("insight", ""),
            "is_knowledge_leader": confluence.get("is_knowledge_leader", False),
            "is_team_enabler": slack.get("is_team_enabler", False),
        },
        "data_completeness": f"{len(sources_available)}/4 sources available"
    }


def generate_signal_narrative(employee_id: str, employee_name: str, role: str) -> str:
    """
    Use Claude to generate a natural language narrative from raw signals.
    This prevents raw number misinterpretation and adds context.
    """
    signals = aggregate_employee_signals(employee_id)
    jira = signals.get("jira", {})
    github = signals.get("github", {})
    confluence = signals.get("confluence", {})
    slack = signals.get("slack", {})
    patterns = signals.get("patterns", {})

    prompt = f"""You are a data analyst specializing in software engineering performance metrics.

Analyze these work signals for {employee_name} ({role}) and write a factual, balanced 150-word narrative that:
1. Summarizes key productivity patterns
2. Highlights standout behaviors (positive or concerning)
3. Flags any invisible contributions (mentoring, documentation, team enablement)
4. Notes any data gaps that should be considered

Raw Signals:
JIRA: tickets_closed={jira.get('tickets_closed','N/A')}, bugs_fixed={jira.get('bugs_fixed','N/A')}, velocity={jira.get('sprint_velocity','N/A')}, on_time={jira.get('on_time_delivery_pct','N/A')}%
GITHUB: prs_merged={github.get('prs_merged','N/A')}, prs_reviewed={github.get('prs_reviewed','N/A')}, review_comments={github.get('review_comments','N/A')}, avg_review_hrs={github.get('avg_review_turnaround_hrs','N/A')}
CONFLUENCE: docs_authored={confluence.get('docs_authored','N/A')}, views={confluence.get('pages_viewed_by_others','N/A')}, comments={confluence.get('comments_received','N/A')}
SLACK: help_responses={slack.get('responses_to_others','N/A')}, help_messages={slack.get('messages_in_help_channels','N/A')}

Patterns detected: reviewer_mentor={patterns.get('is_reviewer_mentor')}, knowledge_leader={patterns.get('is_knowledge_leader')}, team_enabler={patterns.get('is_team_enabler')}

Be specific about numbers. Avoid generic phrases. Flag what's exceptional vs average."""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=400)
    )
    return response.text # FIXED


def aggregate_org_signals() -> dict:
    """
    Aggregate signals across all employees for org-level analytics.
    """
    employees = get_all_employees()
    org_data = {
        "total_employees": len(employees),
        "employees_with_jira": 0,
        "employees_with_github": 0,
        "employees_with_confluence": 0,
        "employees_with_slack": 0,
        "invisible_contributors": [],
        "team_enablers": [],
        "signal_gaps": []
    }

    enablers = detect_team_enablers(employees)
    org_data["team_enablers"] = enablers

    for emp in employees:
        signals = aggregate_employee_signals(emp["id"])
        sources = signals.get("sources_available", [])

        if "jira" in sources:
            org_data["employees_with_jira"] += 1
        if "github" in sources:
            org_data["employees_with_github"] += 1
        if "confluence" in sources:
            org_data["employees_with_confluence"] += 1
        if "slack" in sources:
            org_data["employees_with_slack"] += 1

        # Flag employees with <2 data sources (review quality risk)
        if len(sources) < 2:
            org_data["signal_gaps"].append({
                "employee_id": emp["id"],
                "employee_name": emp.get("name", ""),
                "role": emp.get("role", ""),
                "available_sources": sources,
                "risk": "Review may lack objective evidence — manual input needed"
            })

        # Detect invisible contributors
        patterns = signals.get("patterns", {})
        if any([
            patterns.get("is_reviewer_mentor"),
            patterns.get("is_knowledge_leader"),
            patterns.get("is_team_enabler")
        ]):
            org_data["invisible_contributors"].append({
                "employee_id": emp["id"],
                "employee_name": emp.get("name", ""),
                "patterns": [k for k, v in patterns.items() if v and k != "reviewer_mentor_insight"]
            })

    return org_data


def get_data_quality_report() -> dict:
    """
    Report on data availability and quality across the org.
    Helps HR understand where review quality may be limited.
    """
    org = aggregate_org_signals()
    total = org["total_employees"]

    return {
        "data_coverage": {
            "jira": f"{org['employees_with_jira']}/{total}",
            "github": f"{org['employees_with_github']}/{total}",
            "confluence": f"{org['employees_with_confluence']}/{total}",
            "slack": f"{org['employees_with_slack']}/{total}"
        },
        "signal_gap_employees": org["signal_gaps"],
        "invisible_contributors_count": len(org["invisible_contributors"]),
        "invisible_contributors": org["invisible_contributors"],
        "team_enablers": org["team_enablers"],
        "recommendation": (
            "Employees with <2 data sources need manual manager input "
            "to ensure review quality. Consider expanding integrations for "
            "Sales and Product roles." if org["signal_gaps"] else
            "Good data coverage across all employees."
        )
    }