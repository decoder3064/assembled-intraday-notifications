# Intraday Notification System

Assembled take-home — a system that watches live contact-center events (queue health, agent state, adherence) and notifies the right person when something needs attention, without becoming noise.

- Design spec: [`docs/superpowers/specs/2026-08-05-intraday-notification-system-design.md`](docs/superpowers/specs/2026-08-05-intraday-notification-system-design.md)
- Decision log / reasoning, including the full implementation log (for the walkthrough — this is the most up-to-date narrative): [`decisions.md`](decisions.md)
- Sample data: [`data/events.txt`](data/events.txt)

## What's built

- **Ingestor** (`app/ingestor/`) — validates incoming events, drops duplicates, normalizes inconsistent data.
- **Engine** (`app/engine/`) — evaluates events against rules. 9 rule types implemented: reactive (`queue_backlog`, `sla_risk`, `sla_breach`, `volume_surge`, `zero_coverage`, `adherence_escalated`), duration-based (`long_call`, checked on a timer since nothing reports an in-progress call's length), and one aggregate (`team_adherence_capacity`, tracks violations across multiple agents/events, with its own state that survives the rule-cache refresh — see `decisions.md`). Rules only notify on the ok→firing transition, not on every event. (A 10th type, `adherence_self` — a private nudge to an agent about their own schedule — was built, then deliberately removed once the scope narrowed to team-lead-only; see `decisions.md`.)
- **Persistence** (`app/persistence/`) — `rules`, `rule_state`, `notifications` tables in Postgres.
- **Router** (`app/router/`) — persists notifications and delivers them (console stub for now).
- **API** (`app/api/`) — full CRUD on rules (create/list/edit/delete), notifications (list/resolve/unresolve/delete), and a `/events` endpoint that feeds the running engine. A background poller refreshes the engine's rules from the database every 5 seconds, so a rule created while the server is running takes effect without a restart. The app creates its own database schema on startup, so it works against a genuinely empty database.
- **Frontend** (`frontend/`) — React UI, three panels (Active rules / Notifications / Resolved). Create and edit rules through one modal form with fields that change based on rule type; resolve, undo, and delete notifications. Visual design pulled from Assembled's actual site (colors, font) rather than invented.

## Running it

Start Postgres:
```bash
docker compose up -d db
```

Run the backend test suite (uses its own isolated test database, separate from whatever you're running locally):
```bash
uv run pytest -v
```

Run the frontend test suite:
```bash
cd frontend && npm test
```

Run the API:
```bash
uv run uvicorn app.api.main:app --port 8020 --reload
```
Swagger UI is available at `http://127.0.0.1:8020/docs` for creating/editing rules without the frontend.

Run the frontend:
```bash
cd frontend && npm install && npm run dev
```
Opens on `http://localhost:5190` — CORS on the backend is configured for exactly that origin. If you change either port, update both `app/api/main.py` (CORS origin) and `frontend/vite.config.js` (dev server port) / `frontend/src/api.js` (`BASE_URL`) to match. Ports 8020/5190 were picked because 8000/5173 were already in use during development — pick whatever's free on your machine.

Two demo scripts, both replaying `data/events.txt` at a configurable pace (`--speed`, default 30x — compresses the ~90 real minutes into ~3):
- `uv run python scripts/demo_live.py --base-url http://127.0.0.1:8020` — talks to the real running API and database. Create a rule first (via the frontend or Swagger UI) for it to have something to evaluate — matching the real sample data means a `queue_backlog` rule on queue `billing`, or a `long_call` rule with agent ids `a_31`/`a_11`.
  - **Restart the API server before each re-run.** The ingestor's duplicate-event check lives only in server memory, keyed by each event's fixed ID. Once a run has sent an event_id, the server remembers it for as long as that process stays up — so replaying the same file again against a server that already saw it gets silently treated as duplicates (`200 OK`, zero notifications, no error). Restarting the server (or touching a watched file so `--reload` restarts it) clears that memory for a clean run.
- `uv run python scripts/demo_offline.py` — self-contained, no server or database needed, uses a couple of hardcoded example rules.

## Demo rule sets

`demo_live.py` only produces notifications for rules that actually exist when it runs — the rules below were checked line-by-line against the real timestamps in `data/events.txt`, so each one is guaranteed to fire, and roughly when. Pick **one** set (not both — 4 rules are shared between them, so creating both would create duplicates of those 4), run `docker compose up -d db` and the API server, paste the block, then run `uv run python scripts/demo_live.py --base-url http://127.0.0.1:8020`.

### Set A — billing under pressure, one of every rule type

Why: `billing` is the queue that actually has a bad morning in this dataset — it's the one scenario that shows every reactive rule type escalating on a single queue (coverage drops to zero, occupancy maxes out, the SLA warning fires and then the SLA actually breaches), plus one agent on an unusually long call, one agent whose off-schedule time escalates to the team lead, and the multi-agent aggregate rule. This set has exactly one instance of all 9 implemented rule types, so a single run demonstrates the full catalog.

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

Fire order (at `--speed 30`, ~3 min total): zero coverage + SLA risk ~0:30 → queue backlog ~0:50 → SLA breach + long call ~1:00 → escalated adherence ~1:50 → team adherence capacity ~2:00.

**`volume_surge` is the one exception — it's created above but won't fire during the replay.** Checked it against all three queues across the whole file: actual 15-minute volume never once exceeds the forecast anywhere in this dataset (forecasts always run a bit hot), so no threshold makes it trigger off real data. It's still worth creating so it shows up as a real, working rule in the Active Rules panel — to actually see it fire, send one synthetic event during the demo:
```bash
curl -X POST http://127.0.0.1:8020/events -H "Content-Type: application/json" -d '{"event_id":"evt_demo_surge","ts":"2026-05-26T09:20:00Z","type":"queue_snapshot","queue_id":"billing","tickets_waiting":5,"longest_wait_sec":30,"sla_target_sec":120,"agents_available":2,"agents_on_call":2,"volume_last_15m":40,"volume_forecast_next_15m":20}'
```

### Set B — spread across all three queues

Why: Set A makes it look like this only works for `billing`. This set proves the same rule types generalize to `tier_2` and `vip` too — including a risk→breach escalation on `tier_2` (the same pattern billing shows), and one rule on `vip`, which barely misbehaves in this dataset at all (worth saying out loud in the demo — a queue that mostly stays healthy is a real, useful case to show, not just the queues that are on fire).

```bash
curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"zero_coverage","scope":{"queue_id":"billing"},"params":{},"severity":9,"description":"Notify me when nobody'"'"'s free in billing and tickets are waiting"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"sla_breach","scope":{"queue_id":"billing"},"params":{},"severity":9,"description":"Notify me when billing has already missed its SLA"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"long_call","scope":{"agent_ids":["a_11"]},"params":{"duration_min":20},"severity":9,"description":"Notify me if any of Agent 11 has been on one call for over 20 minutes"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"sla_risk","scope":{"queue_id":"tier_2"},"params":{"pct_of_sla":0.75},"severity":5,"description":"Warn me when tier_2 is close to missing its SLA (75%)"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"queue_backlog","scope":{"queue_id":"tier_2"},"params":{"threshold":3},"severity":5,"description":"Notify me when tier_2 has more than 3 tickets waiting"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"sla_risk","scope":{"queue_id":"vip"},"params":{"pct_of_sla":0.5},"severity":5,"description":"Warn me when vip is close to missing its SLA (50%)"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"sla_breach","scope":{"queue_id":"tier_2"},"params":{},"severity":9,"description":"Notify me when tier_2 has already missed its SLA"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"occupancy","scope":{"queue_id":"tier_2"},"params":{"occupancy_threshold":0.8},"severity":5,"description":"Notify me when tier_2'"'"'s occupancy crosses 80%"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"team_adherence_capacity","scope":{"agent_ids":["a_19","a_88"]},"params":{"count_threshold":1},"severity":9,"description":"Notify me when more than 1 of Agent 19 and Agent 88 are off-schedule at the same time"}'

curl -X POST http://127.0.0.1:8020/rules -H "Content-Type: application/json" -d '{"rule_type":"adherence_escalated","scope":{"agent_ids":["a_88"]},"params":{"duration_min":10},"severity":9,"description":"Notify me if any of Agent 88 has been off-schedule for over 10 minutes and hasn'"'"'t fixed it"}'
```

Fire order: zero coverage (billing) + SLA breach (billing) + long call ~1:00 → SLA risk (tier_2) + queue backlog (tier_2) ~1:30 → SLA risk (vip) ~1:38 → SLA breach (tier_2) + occupancy (tier_2) + team adherence capacity ~2:00 → escalated adherence (Agent 88) ~2:30.

`volume_surge` isn't in Set B — see the note under Set A above for why it can't fire off real replay data regardless of which set it's in, and the synthetic event that demos it anyway.

## Not built yet

- `rule_state` isn't persisted — see the comment on `RuleStateRow` in `app/persistence/models.py` for why, and what a production fix would look like.
- The more general "diff the rule-cache poller instead of a per-rule hook" fix — see `decisions.md` for the reasoning on why the narrower fix was chosen instead.
- Auth, multi-tenancy, and real Slack/email delivery — explicitly out of scope per the prompt.
