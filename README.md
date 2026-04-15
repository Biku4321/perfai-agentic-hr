<div align="center">

```
██████╗ ███████╗██████╗ ███████╗ █████╗ ██╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██╔══██╗██║
██████╔╝█████╗  ██████╔╝█████╗  ███████║██║
██╔═══╝ ██╔══╝  ██╔══██╗██╔══╝  ██╔══██║██║
██║     ███████╗██║  ██║██║     ██║  ██║██║
╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝
```

### **Agentic Performance Layer on effiHR**
*From "system of record" → "intelligent system of action"*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash_Lite-4285F4?logo=google&logoColor=white)](https://aistudio.google.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## The Problem

Every organization runs appraisal cycles. Almost none do them well.

Goals aren't tracked. Managers rush reviews. Feedback is vague, inconsistent, biased. High performers leave because nobody noticed. HR spends weeks chasing completion. And when the dust settles, the system of record has a number in a field — with no story behind it.

**PerfAI fixes this.** Not with a chatbot. With a mesh of autonomous agents that *proactively act* — aggregating real work signals, drafting evidence-backed reviews, nudging at the right moment, and surfacing invisible contributors before the cycle closes.

---

## What Makes This Different

| The Old Way | The PerfAI Way |
|---|---|
| Manager recalls last 2 weeks | Full-cycle signal from Jira, GitHub, Confluence, Slack |
| "Good team player" feedback | "Reviewed 54 PRs, 187 comments, 4.2hr avg turnaround" |
| HR chasing completion via email | Agents predict risk and nudge proactively |
| Invisible contributors ignored | Detected automatically via behavioral patterns |
| Bias undetected | Statistical radar flags inconsistencies before they're submitted |
| Employees guess what to write | Self-assessment coach builds talking points from their own signals |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL WORK SIGNALS                          │
│   Jira / Linear   GitHub / GitLab   Confluence / Notion   Slack      │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │    DATA     │  Normalize · De-bias · Vectorize
                    │   AGENT     │  → ChromaDB RAG store
                    └──────┬──────┘
                           │
            ┌──────────────▼──────────────┐
            │    HR ORCHESTRATION AGENT   │  ← Supervisor
            │  Cycle health · Bias radar  │
            │  Deadline prediction · Risk │
            └────┬──────────┬────────┬───┘
                 │          │        │
         ┌───────▼──┐  ┌────▼───┐  ┌▼──────────┐
         │ MANAGER  │  │  EMP.  │  │ ANALYTICS │
         │  AGENT   │  │ COACH  │  │   AGENT   │
         │          │  │        │  │           │
         │ • Drafts │  │ • Self │  │ • Trends  │
         │ • Nudges │  │   asmt │  │ • Fairness│
         │ • Bias   │  │ • Goal │  │ • Reports │
         │   flags  │  │   gaps │  │           │
         └────┬─────┘  └────┬───┘  └─────┬─────┘
              │             │             │
         ┌────▼─────────────▼─────────────▼────┐
         │         effiHR CORE (SQLite/PG)      │
         │  Goals · Attendance · Ratings ·      │
         │  Appraisal Cycles · Profiles         │
         └────────────────┬─────────────────────┘
                          │
         ┌────────────────▼─────────────────────┐
         │              UX SURFACES              │
         │  In-product chat  │  Slack nudge bot  │
         │  HR dashboard     │  Email digest     │
         └──────────────────────────────────────┘
```

---

## Agents In Detail

### 🔵 Data Aggregation Agent
The foundation. Pulls and normalizes signals from every external system, contextualizes them against HR data, and writes them into a vector store for semantic retrieval.

- **Connectors**: Jira REST API, GitHub API, Confluence API, Slack Events API
- **Normalization**: Role-aware scoring — engineer metrics ≠ sales metrics
- **Context enrichment**: Relative to team, tenure, and historical baseline
- **Anti-bias filter**: Strips PII patterns before aggregation

### 🟣 HR Orchestration Agent *(Supervisor)*
The brain. Monitors the entire appraisal cycle and decides what to act on — without being asked.

- **Cycle health monitoring**: Completion rate, velocity, trajectory
- **Deadline prediction**: Flags at-risk managers 10 days early, not 10 hours
- **Bias radar**: Statistical analysis of ratings vs output signals; recency bias detection
- **Invisible contributor discovery**: Finds mentoring, code reviews, docs that never appear in ticket counts
- **Escalation routing**: Knows when to nudge, when to escalate to HR, when to auto-generate

### 🟠 Manager Assistant Agent
The time-saver. Turns 45-minute rushed reviews into 15-minute thoughtful ones.

- **Evidence-based draft generation**: Grounds every claim in specific data — no generic language
- **Source attribution**: Every draft section tagged with its signal origin (Jira / GitHub / Confluence / Slack)
- **Personalized nudges**: AI-crafted Slack/email messages timed contextually, not cron-blasted
- **Inline bias warnings**: Flags patterns before the manager submits

### 🟢 Employee Coach Agent
The self-advocate. Helps employees articulate impact they didn't know was measurable.

- **Signal-driven talking points**: Pulls the employee's own Jira, GitHub, Confluence, Slack data
- **First-person framing**: Converts raw metrics into confident, specific claims
- **Goal gap alerts**: Surfaces misaligned or stalled goals weeks before cycle closes
- **Growth area suggestions**: Recommends honest development areas that signal self-awareness

### 🟡 HR Analytics Agent
The strategist. Gives HR leadership the visibility they've never had before.

- **Real-time completion dashboard**: Live cycle health, not end-of-cycle postmortems
- **Fairness reports**: Cross-manager, cross-department rating pattern analysis
- **Nudge audit log**: Full history of every agent-triggered communication
- **Cycle improvement insights**: What drove quality reviews vs rushed ones

---

## Core Capabilities

### Evidence-Based Review Drafts

```bash
POST /api/reviews/generate-draft
{
  "employee_id": "E001",
  "cycle_id": "CYC-2024-H1",
  "manager_context": "Led the API migration initiative"
}
```

The agent queries all signal sources, retrieves the employee's full-cycle history, and produces:

```
## Executive Summary
Priya has delivered outsized impact this cycle across delivery, peer enablement,
and knowledge-sharing — making her influence broader than individual output metrics suggest.

## Key Achievements
• API Latency Reduction: 30% reduction ahead of deadline. (Goal: ✓ 100%)
  Source: Jira [47 tickets, 89% on-time] + GitHub [31 PRs merged]
• Code Review Leadership: Reviewed 54 PRs with 187 comments, avg 4.2hr turnaround.
  Unblocked 3 junior engineers. Source: GitHub
• Knowledge Multiplier: Authored 8 docs viewed 320+ times. Source: Confluence

## ⚠ Invisible Contribution Flag
PerfAI detected 124 Slack help responses this cycle. This peer-enabling work
is NOT captured in goal tracking. Recommend explicit recognition.

## Suggested Rating: 4.6 / 5.0
Justification: Top-quartile output + measurable peer impact at her level.
```

### Proactive Nudging

The agent autonomously identifies risk and crafts context-aware messages — not generic reminders:

```
Hey Vikram! You have 2 reviews due in 5 days. Good news — PerfAI has
pre-generated evidence-based drafts for Priya and Arjun. Should take
~15 min to review and personalize. Want me to open them? 🚀
```

### Invisible Contributor Detection

Three classes of under-recognized work, detected automatically:

| Signal Type | Detection Logic | Example |
|---|---|---|
| **Code mentorship** | `prs_reviewed / prs_authored > 1.5` | Reviews 54 PRs, only merged 31 own |
| **Knowledge multiplier** | `docs_authored ≥ 5 AND doc_views > 200` | 15 docs viewed 890+ times |
| **Team enablement** | `help_channel_responses > 80` | 124 Slack responses in #help channels |

### Bias Radar

Statistical checks run before any review is submitted:

```python
checks = [
    "recency_bias",            # Did manager only reference last sprint?
    "gender_rating_disparity", # Cross-team rating pattern analysis
    "high_performer_neglect",  # Stars getting rushed reviews
    "invisible_work_ignored",  # Behavioral signals vs output signals gap
    "rating_vs_output_gap"     # Submitted rating inconsistent with data
]
```

---

## Data & Signals

### Signal Schema

```json
{
  "employee_id": "E001",
  "sources": {
    "jira": {
      "tickets_closed": 47,
      "bugs_fixed": 12,
      "sprint_velocity": 42,
      "on_time_delivery_pct": 89
    },
    "github": {
      "prs_merged": 31,
      "prs_reviewed": 54,
      "review_comments": 187,
      "avg_review_turnaround_hrs": 4.2
    },
    "confluence": {
      "docs_authored": 8,
      "pages_viewed_by_others": 320
    },
    "slack": {
      "responses_to_others": 124,
      "messages_in_help_channels": 89
    }
  }
}
```

### Role-Aware Scoring

| Role | Primary Signals | Secondary Signals |
|---|---|---|
| Software Engineer | GitHub PRs, Jira velocity, review quality | Confluence docs, Slack mentoring |
| DevOps / Infra | Ops tickets, incident response time | Documentation, runbooks authored |
| Product Manager | Confluence roadmaps, cross-team alignment | Goal completion, stakeholder signals |
| Sales | CRM deal velocity, pipeline value, win rate | Slack collaboration, enablement content |
| Operations | Ticket SLA compliance, process docs | Cross-team coordination signals |

---

## API Reference

### Employees

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/employees` | List all employees |
| `GET` | `/api/employees/{id}` | Profile + goals + signals + attendance |
| `GET` | `/api/employees/{id}/signals` | Raw work signals |
| `GET` | `/api/employees/{id}/self-assessment-help` | AI-generated talking points |

### Appraisal Cycle

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cycle` | Current cycle with all review statuses |
| `GET` | `/api/cycle/health` | Completion rate, velocity, AI-assist rate |
| `GET` | `/api/cycle/risk` | Manager deadline risk prediction with scores |

### Review Drafts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/reviews/generate-draft` | Generate evidence-based AI review draft |
| `GET` | `/api/reviews/{employee_id}/{cycle_id}` | Retrieve existing review + draft |

### Manager Operations

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/managers/{id}/team` | Team view with signal sources and statuses |
| `POST` | `/api/managers/nudge` | Trigger personalized nudge for a manager |

### HR Analytics & Orchestration

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/hr/dashboard` | Full HR summary report with AI narrative |
| `GET` | `/api/hr/bias-flags` | Active fairness and bias flags |
| `GET` | `/api/hr/nudge-log` | Audit log of all agent communications |
| `POST` | `/api/agents/run-cycle-scan` | Full orchestrator scan: drafts + nudges + bias |

### Agent Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Conversational agent — ask anything about your team |

Interactive Swagger docs: `http://localhost:8000/docs`

---

## Quick Start

### Prerequisites

- [Docker](https://docker.com) + Docker Compose
- An [Google Gemini API key](https://aistudio.google.com)

### One-command launch

```bash
git clone https://github.com/yourteam/perfai && cd perfai

cp .env.example .env


docker compose up --build
```

| Service | URL |
|---|---|
| Frontend app | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

### Local development (no Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              
uvicorn api.main:app --reload --port 8000

# Frontend — new terminal
cd frontend
open index.html                   
```

### Environment Variables

```bash
# ── Required ─────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...

# ── Integrations (mock data used if omitted) ─────────────
JIRA_BASE_URL=https://yourorg.atlassian.net
JIRA_EMAIL=you@yourorg.com
JIRA_API_TOKEN=...

GITHUB_TOKEN=ghp_...

CONFLUENCE_BASE_URL=https://yourorg.atlassian.net/wiki
CONFLUENCE_TOKEN=...

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_BOT_TOKEN=xoxb-...

# ── Database (SQLite default, Postgres for production) ────
DATABASE_URL=sqlite:///./data/effihr.db
# DATABASE_URL=postgresql://user:password@db:5432/perfai

# ── Server ────────────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
```

---

## Project Structure

```
perfai/
│
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py        # HR supervisor · bias detection · cycle health
│   │   └── manager_agent.py       # Draft generation · nudges · self-assessment
│   │
│   ├── connectors/                # Extensible external system adapters
│   │   ├── jira_connector.py
│   │   ├── github_connector.py
│   │   ├── confluence_connector.py
│   │   └── slack_connector.py
│   │
│   ├── core/
│   │   └── effihr_db.py           # Data access layer (SQLite / Postgres)
│   │
│   ├── api/
│   │   └── main.py                # FastAPI app · all routes · CORS middleware
│   │
│   ├── data/
│   │   └── seed_data.json         # Mock employees, goals, signals, cycle
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── index.html                 # Full SPA · works offline with mock data
│
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

---

## Success Metrics

| Metric | Industry Baseline | With PerfAI |
|---|---|---|
| Cycle completion rate | ~58% on time | **95%+** |
| Avg manager time per review | 45 min | **12–15 min** |
| Reviews with specific evidence | ~20% | **90%+** |
| Invisible contributions captured | <5% | **70%+** |
| Bias flags detected before submit | ~0% (manual) | **Automated** |
| HR chasing effort | High | **Near-zero** |

---

## Privacy & Ethics

PerfAI is built with a clear principle: **AI assists, humans decide.**

- **Data minimization**: Work signals are aggregated; raw activity logs are never surfaced to managers
- **Role-based access**: Employees see only their own signals; managers see only their team
- **Editable drafts**: All AI-generated content is a suggestion — every review is reviewed and submitted by a human
- **Full audit trail**: Every agent action (draft generated, nudge sent, flag raised) is logged with timestamp and rationale
- **No surveillance**: Slack signals measure collaborative patterns, not message content
- **Consent-aware**: Data sources are configured by the organization; employees are informed of what's integrated

---

## Roadmap

- [ ] Full ChromaDB vector RAG integration for semantic signal retrieval across cycles
- [ ] Plug-and-play connectors for Linear, Notion, HubSpot, Salesforce
- [ ] Multi-cycle trend analysis (rating trajectory across 4+ cycles)
- [ ] Calibration assistant — cross-manager rating normalization in real time
- [ ] 360 signal fusion — peer feedback aggregation and synthesis
- [ ] LangGraph stateful workflows with human-in-the-loop checkpoints
- [ ] Enterprise SSO + RBAC with granular permission model

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **LLM** | Gemini
Gemini-2.5-flash-lite | Best-in-class instruction following, long context, safe outputs |
| **Backend** | FastAPI + Python 3.11 | Async-native, auto-docs, type-safe |
| **Agent Framework** | Gemini Messages API + custom orchestration | Full control over agentic loops |
| **Vector Store** | ChromaDB | Lightweight no-infra RAG for signal retrieval |
| **Database** | SQLite → PostgreSQL | Zero-setup dev, production-grade path |
| **Frontend** | Vanilla JS + CSS | Instant load, zero build step for demo |
| **Scheduler** | APScheduler | Proactive triggers — deadline scans, nudge batches |
| **Notifications** | Slack Webhooks + SMTP | Where managers actually work |
| **Containers** | Docker + Docker Compose | One-command dev and deploy |

---

<div align="center">

*PerfAI — because performance reviews should reflect performance, not recall.*

**Built for the effiHR Hackathon · 2026**

</div>