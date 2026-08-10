# Intraday Notification System

Watches live contact-center data (queue health, agent status, schedule adherence) and notifies a team lead when something needs attention — without becoming noise.

## Scope

Built for the **team lead** overseeing one team — queue health, agent status, and schedule adherence, all in one place.

## Architecture

```mermaid
flowchart LR
    Events[Events] --> Ingestor[Ingestor]
    Ingestor --> Engine[Engine]
    Engine --> Router[Router]
    Router --> Notifications[("Notifications<br/>(Postgres)")]

    Frontend[Frontend] -->|create / edit rules| API[API]
    API --> Rules[("Rules<br/>(Postgres)")]
    Rules -->|refreshed every 5s| Engine

    Notifications -->|polled| Frontend
```

- **Ingestor** — validates and normalizes incoming events, drops duplicates.
- **Engine** — checks events against the current rules. Also runs a periodic check for rules that depend on elapsed time rather than a new event arriving (e.g. "this agent has been on one call for 20 minutes" — nothing tells you a call is *still* going, so the engine checks in on its own).
- **Router** — decides who gets notified, persists the notification, hands it to delivery (console for now).
- **Rules live in Postgres, not in code** — changing a threshold is a form, not a deploy. The Engine keeps its own in-memory copy, refreshed from the database every 5 seconds, so a rule created through the frontend takes effect without restarting anything.

## Data model

**`rules`**

| column | type | notes |
|---|---|---|
| id | uuid | |
| rule_type | text | one of the 9 catalog values, checked against a registry in code, not a DB enum — adding a type is a code change, not a migration |
| scope | jsonb | what the rule watches, e.g. `{"queue_id": "billing"}` or `{"agent_ids": [...]}` |
| params | jsonb | rule-type-specific thresholds, e.g. `{"threshold": 20}` |
| recipient_id | text | always the one team lead (see Scope) — kept as a generic person id rather than removed, so multi-recipient support later is a small change, not a rewrite |
| description | text | auto-rendered from a per-rule-type template, not typed freely |
| severity | int | shown as Low/Medium/High in the UI, stored as an int |
| enabled | boolean | |
| created_at, updated_at | timestamp | |

**`notifications`** — the output log, and what the notifications panel reads from.

| column | type | notes |
|---|---|---|
| id | uuid | |
| rule_id | uuid → rules.id, nullable | set to null (not cascaded) if the rule is later deleted, so notification history survives |
| rule_type | text | snapshotted at creation time, so it also survives the rule being deleted |
| recipient_id | text | |
| message | text | rendered from the rule's message template plus the triggering event's live data |
| severity | int | shown as Low/Medium/High in the UI, stored as an int |
| resolved | boolean | defaults to false; set by the team lead marking it handled in the UI, not by the system |
| sent_at | timestamp | |

## Rule catalog

9 rule types, each reacting to a different signal:

| Rule | Fires when |
|---|---|
| Queue backlog | Too many tickets waiting in a queue |
| SLA at risk | A wait is getting close to the promised max wait time |
| SLA breached | A wait has already passed the promised max |
| Volume surge | Call volume is running well above what was forecasted |
| Zero coverage | Nobody's free in a queue and tickets are waiting |
| Occupancy | Most of a queue's agents are tied up on calls, even before a backlog forms |
| Long call | One agent's been on the same call too long |
| Escalated adherence | One agent's been off schedule too long |
| Team adherence capacity | Too many agents are off schedule at the same time |

A rule only notifies once, on the transition from "fine" to "a problem" — not repeatedly while the problem is ongoing.

## Known, deliberate gaps

- **No-repeat-alert state is in-memory only.** A restart can cause one duplicate notification for whatever was already firing at that moment.

---

## Setup

### Ports

| Service | URL |
|---|---|
| Frontend | `http://localhost:5190` |
| Backend API | `http://localhost:8020` (Swagger docs at `/docs`) |
| Postgres | `localhost:5433` (Docker) or `localhost:5432` (local install) |

### Prerequisites

- **Docker** (simplest path, below) — or, to run without it: **Python 3.12+** + **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (`curl -LsSf https://astral.sh/uv/install.sh | sh`, or `brew install uv`), **Node.js 22+** + npm, and **Postgres**

### Run it: with Docker

One command starts everything — Postgres, the backend, and the frontend:
```bash
docker compose up --build
```
Frontend: `http://localhost:5190`. API: `http://localhost:8020`.

### Run it: without Docker

Install Postgres 16 locally if you don't have it:
```bash
brew install postgresql@16 && brew services start postgresql@16   # macOS
# or: sudo apt install postgresql && sudo systemctl start postgresql
```

Create the database and user the app expects:
```bash
createuser app -P    # set password to "app" when prompted
createdb notifications -O app
```

Local Postgres usually listens on port 5432, not 5433 (the port the Docker setup uses to avoid conflicting with a local install) — point the app at wherever yours actually runs:
```bash
export DATABASE_URL="postgresql+asyncpg://app:app@localhost:5432/notifications"
uv run uvicorn app.api.main:app --port 8020 --reload
```

Then, same as above:
```bash
cd frontend && npm install && npm run dev
```

### Tests
```bash
uv run pytest -v            # backend
cd frontend && npm test     # frontend
```

### See it work

Two scripts replay the sample data (`data/events.txt`) at a sped-up pace:

- **`uv run python scripts/demo_offline.py`** — fully self-contained. No server, no database. Fastest way to confirm the rule logic works.
- **`uv run python scripts/demo_live.py --base-url http://127.0.0.1:8020`** — talks to your actual running API and database. Create a rule first (in the UI or Swagger), then run this and watch notifications appear live in the frontend.

**Restart the API before re-running `demo_live.py`.** Duplicate-event detection lives in server memory — replaying the same file against a server that already saw it produces zero new notifications, silently.

#### Ready-to-paste rule set

Creates one instance of every rule type, scoped to the `billing` queue, guaranteed to fire against the real sample data (verified against the actual timestamps in `data/events.txt`):

```bash
curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"zero_coverage","scope":{"queue_id":"billing"},"params":{},"severity":9,"description":"Notify me when nobody'"'"'s free in billing and tickets are waiting"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"occupancy","scope":{"queue_id":"billing"},"params":{"occupancy_threshold":0.8},"severity":5,"description":"Notify me when billing'"'"'s occupancy crosses 80%"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"sla_risk","scope":{"queue_id":"billing"},"params":{"pct_of_sla":0.7},"severity":5,"description":"Warn me when billing is close to missing its SLA (70%)"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"queue_backlog","scope":{"queue_id":"billing"},"params":{"threshold":10},"severity":5,"description":"Notify me when billing has more than 10 tickets waiting"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"sla_breach","scope":{"queue_id":"billing"},"params":{},"severity":9,"description":"Notify me when billing has already missed its SLA"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"long_call","scope":{"agent_ids":["a_11"]},"params":{"duration_min":20},"severity":9,"description":"Notify me if any of Agent 11 has been on one call for over 20 minutes"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"adherence_escalated","scope":{"agent_ids":["a_19"]},"params":{"duration_min":20},"severity":9,"description":"Notify me if any of Agent 19 has been off-schedule for over 20 minutes and hasn'"'"'t fixed it"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"team_adherence_capacity","scope":{"agent_ids":["a_19","a_88"]},"params":{"count_threshold":1},"severity":9,"description":"Notify me when more than 1 of Agent 19 and Agent 88 are off-schedule at the same time"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"volume_surge","scope":{"queue_id":"billing"},"params":{"pct_over_forecast":0.1},"severity":9,"description":"Notify me when billing'"'"'s volume is running well above what was forecasted (>10%)"}'
```

At the default `--speed 9` (~10 demo minutes for ~90 real minutes), everything fires within the first 7 minutes except `volume_surge` — real call volume never exceeds forecast anywhere in the sample data, so that one rule is correctly implemented but can't be proven from the replay alone. To see it fire, send one synthetic event:
```bash
curl -X POST http://127.0.0.1:8020/events -H "Content-Type: application/json" -d '{"event_id":"evt_demo_surge","ts":"2026-05-26T09:20:00Z","type":"queue_snapshot","queue_id":"billing","tickets_waiting":5,"longest_wait_sec":30,"sla_target_sec":120,"agents_available":2,"agents_on_call":2,"volume_last_15m":40,"volume_forecast_next_15m":20}'
```

### Project layout

```
app/ingestor/     validates and normalizes incoming events
app/engine/       rule evaluation
app/engine/rules/ the 9 rule types
app/persistence/  database models
app/router/       delivers notifications (console for now)
app/api/          FastAPI app
frontend/         React UI
data/events.txt   sample event feed used by the demo scripts
```

## AI usage

Built with Claude Code for architecture discussion, implementation, and documentation, which I reviewed and approved throughout. Used ChatGPT for research on the domain and the end user. For product decisions I grounded my thinking in a real conversation, not just AI or the prompt: I interviewed a team lead at a customer service company (my cousin) to understand what actually matters day to day. Every scope decision, what to build, what to cut, and every design choice was mine, made after reviewing what was proposed.
