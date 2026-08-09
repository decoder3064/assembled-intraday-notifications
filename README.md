# Intraday Notification System

Assembled take-home — a system that watches live contact-center events (queue health, agent state, adherence) and notifies the right person when something needs attention, without becoming noise.

- Design spec: [`docs/superpowers/specs/2026-08-05-intraday-notification-system-design.md`](docs/superpowers/specs/2026-08-05-intraday-notification-system-design.md)
- Decision log / reasoning, including the full implementation log (for the walkthrough — this is the most up-to-date narrative): [`decisions.md`](decisions.md)
- Sample data: [`data/events.txt`](data/events.txt)

## What's built

- **Ingestor** (`app/ingestor/`) — validates incoming events, drops duplicates, normalizes inconsistent data.
- **Engine** (`app/engine/`) — evaluates events against rules. All 10 designed rule types implemented: reactive (`queue_backlog`, `sla_risk`, `sla_breach`, `volume_surge`, `zero_coverage`, `adherence_self`, `adherence_escalated`), duration-based (`long_call`, checked on a timer since nothing reports an in-progress call's length), and one aggregate (`team_adherence_capacity`, tracks violations across multiple agents/events, with its own state that survives the rule-cache refresh — see `decisions.md`). Rules only notify on the ok→firing transition, not on every event.
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

Two demo scripts, both replaying `data/events.txt` at a configurable pace (`--speed`, default 18x — compresses the ~90 real minutes into ~5):
- `uv run python scripts/demo_live.py --base-url http://127.0.0.1:8020` — talks to the real running API and database. Create a rule first (via the frontend or Swagger UI) for it to have something to evaluate — matching the real sample data means a `queue_backlog` rule on queue `billing`, or a `long_call` rule with agent ids `a_31`/`a_11`.
- `uv run python scripts/demo_offline.py` — self-contained, no server or database needed, uses a couple of hardcoded example rules.

## Not built yet

- `rule_state` isn't persisted — see the comment on `RuleStateRow` in `app/persistence/models.py` for why, and what a production fix would look like.
- The more general "diff the rule-cache poller instead of a per-rule hook" fix — see `decisions.md` for the reasoning on why the narrower fix was chosen instead.
- Auth, multi-tenancy, and real Slack/email delivery — explicitly out of scope per the prompt.
