# PerfAI — Agentic Performance Layer on effiHR

> "From HRMS as a system of record → HRMS as an intelligent system of action"

## 🏆 Hackathon Overview

PerfAI is a **multi-agent AI system** built on top of effiHR that transforms the performance appraisal cycle from a reactive, manual process into an **intelligent, proactive workflow**.

---

## 🤖 Agent Architecture

```
External Signals (Jira, GitHub, Confluence, Slack, CRM)
          ↓
  [Data Aggregation Agent]  ← normalizes, contextualizes, vectorizes
          ↓
  [HR Orchestration Agent]  ← supervisor: monitors, detects bias, escalates
    ↙        ↓         ↘
[Manager   [Employee   [HR Analytics
 Agent]     Coach]      Agent]
          ↓
     effiHR Core (SQLite / Postgres)
          ↓
   UX: Dashboard | Slack Bot | Email | In-product Chat
```

### Agent Roles

| Agent | Proactive Actions |
|---|---|
| **Data Aggregation** | Scheduled ETL from Jira/GitHub/Confluence APIs; vectorizes into ChromaDB |
| **HR Orchestration** | Cycle deadline tracking; bias detection; invisible contributor discovery; escalation |
| **Manager Assistant** | Auto-drafts evidence-based reviews; generates smart deadline nudges |
| **Employee Coach** | Generates self-assessment talking points; surfaces goal gaps |
| **HR Analytics** | Completion rates; fairness reports; performance band suggestions |

---

## ⚡ Key Features

### 1. Evidence-Based Review Drafts
- Auto-generates review drafts grounded in Jira velocity, GitHub PRs, Confluence docs, Slack activity
- Manager sees: "Priya closed 47 tickets at 89% on-time, reviewed 54 PRs..." not "good team player"
- Editable drafts with evidence source tags

### 2. Invisible Contributor Detection  
- Finds mentoring in Slack help channels
- Surfaces documentation impact (views × quality)
- Flags high PR-review-to-PR-author ratios (code mentors)

### 3. Bias Radar
- Statistical comparison of ratings vs output signals
- Recency bias detection (was only last sprint considered?)
- High-performer risk (stars with delayed reviews)
- Gender/dept rating pattern analysis

### 4. Proactive Nudging
- AI-generated personalized Slack/email nudges
- Predicts deadline risk 10 days out
- Tailors message ("draft is ready, takes 15 min") not just "review due"

### 5. Self-Assessment Coach
- Pulls employee's own signals to suggest talking points
- First-person, impact-focused language
- Proactively suggests growth areas for self-awareness credit

---

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key" > .env
uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
# Open index.html in browser (works standalone with mock data)
# Or serve with: python -m http.server 3000
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/cycle/health` | GET | Cycle completion metrics |
| `/api/cycle/risk` | GET | Manager deadline risk prediction |
| `/api/reviews/generate-draft` | POST | Generate AI review draft |
| `/api/hr/dashboard` | GET | Full HR summary with AI narrative |
| `/api/hr/bias-flags` | GET | Active bias and fairness flags |
| `/api/managers/nudge` | POST | Send personalized nudge |
| `/api/employees/{id}/self-assessment-help` | GET | AI self-assessment coach |
| `/api/agents/run-cycle-scan` | POST | Full orchestrator scan |
| `/api/chat` | POST | Conversational agent interface |

---

## 📊 Success Metrics

| Metric | Baseline | With PerfAI |
|---|---|---|
| Cycle completion rate | 60% | 95%+ |
| Avg manager time per review | 45 min | 15 min |
| Reviews with specific evidence | 20% | 90%+ |
| Invisible contributions captured | 5% | 70%+ |
| Bias flags detected | Manual / 0 | Automated |
| HR chasing effort | High | Near-zero |

---

## 🔒 Ethics & Privacy

- Work signals used for **aggregated context**, never raw surveillance
- All AI drafts are **editable suggestions**, manager has final say
- Bias detection flags **patterns**, not individuals
- Data access follows **role-based permissions**
- Audit log for all agent actions

---

## 🏗 Tech Stack

- **Backend**: FastAPI + Python
- **Agents**: Anthropic Claude claude-sonnet-4-20250514 (claude-sonnet-4-20250514)
- **Vector DB**: ChromaDB (RAG for work signals)  
- **Database**: SQLite (mock effiHR) / Postgres (prod)
- **Frontend**: Vanilla JS + modern CSS (zero-dependency demo)
- **Scheduler**: APScheduler for proactive triggers
- **Notifications**: Slack Webhooks + SMTP

---

## 📁 Folder Structure

```
perfai/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py      # HR supervisor + bias detection
│   │   └── manager_agent.py     # Draft generation + nudges
│   ├── core/
│   │   └── effihr_db.py         # SQLite data layer
│   ├── data/
│   │   └── seed_data.json       # Mock HR + work signal data
│   ├── api/
│   │   └── main.py              # FastAPI routes
│   └── requirements.txt
├── frontend/
│   └── index.html               # Full SPA (works offline)
└── README.md
```