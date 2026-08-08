# Decisions Log — quick version

## The basics
- Rules live in the database, not buried in code — so someone can change a threshold without needing a new deploy. If a team lead wants "20 tickets" to become "15," that's a form, not an engineering ticket.
- Split into three simple pieces: one takes in the data, one checks it against the rules, one sends the alert. Each piece stays simple and can be tested on its own without dragging the other two along.
- Used tools I already know well (FastAPI, Postgres) so my time went into the hard problems, not learning a new framework. Kept the frontend tiny on purpose — just a list of rules and a form to edit them, no login system, no fancy drag-and-drop builder.
- Keep the rules sitting in memory instead of hitting the database on every single event — too slow once you're talking millions of events a day. Refresh that memory every few seconds instead of chasing instant updates (more on why below — that's one of the two things I want to explain properly).
- Some things can't be caught just by reacting to events — like "this agent has been on one call for 45 minutes." Nothing tells you that while the call's still going, the system only hears about it once the call ends. So on top of reacting to events, it also checks in on its own every so often, just to catch things that are true because time passed, not because something happened.
- Don't repeat the same alert over and over while a problem is still ongoing — only alert once, right when it starts. Otherwise a queue that's backed up for twenty minutes pings someone forty times instead of once.
- Built for team leads and agents — team lead is the main experience (a command-center view covering their queues and their whole team, including individual agent metrics like adherence and call length, not just aggregate numbers), agents get a lighter, self-service layer for their own adherence. Decided against splitting them into two heavy separate builds — since a rule is just "a condition + who gets told," adding agents as a possible recipient didn't cost a new engine or new tables, just one more simple form. Skipped head-of-support on purpose — that's a different feature entirely (a rolled-up summary, not a real-time alert), left out and named as a cut, not built half-way. Rule table itself doesn't hardcode "team lead" anywhere — the recipient is just a person, so this stays flexible on purpose.
- The sample data had real messiness — one event repeated itself, and one showed up about an hour late. That's normal in real systems, not a bug in the data. Built two small checks for it: skip anything already seen, and never let old information overwrite something newer that already arrived.
- Also noticed "no queue" gets written two different ways in the data — sometimes `null`, sometimes an empty list — same meaning, different shape. Fixed by cleaning it up to one shape as soon as it comes in, so nothing later in the system has to check for both.

## Why "check every few seconds" beats "instant updates"
Instant updates need a connection that stays open the whole time, listening for changes. The problem is that kind of connection can quietly die — a network blip, a restart, whatever — and nothing tells you it broke. You'd have to build extra code just to notice that and reconnect. All that extra work buys you one thing: a rule change takes effect instantly instead of a few seconds later. Nobody's sitting there needing it that fast — an ops manager editing a threshold doesn't care if it's live in one second or three. Checking every few seconds gets the same result, is simpler to build, has way less that can break, and nobody would ever notice the difference.

## The "late, but maybe still true" question
One event in the sample showed up about an hour late — not broken, just delayed, the way messages sometimes are in real systems. My rule for handling that: never let old information overwrite something newer you already have. That part's solid and it's in the code. But it raised a fair question — what if nothing newer has come in yet? Is that late information actually still useful, or just noise? I didn't build the fancier version of that (checking whether the situation has already changed before deciding to alert on it) because it only shows up once in the sample data, and chasing it would've eaten time for very little payoff on a project this size. But it's a real limitation, not something I missed — worth saying out loud in the presentation as a "here's what I'd build next" instead of pretending it isn't there.

---

# Implementation Log

Everything below happened after the design above was approved and we started actually building. Kept separate from the design section since this is "what got built and what came up while building it," not "what we planned."

## What actually got built, in order

1. **Ingestor** (`app/ingestor/`) — Pydantic models per event type (`schemas.py`), idempotency (drops duplicate `event_id`s), null normalization. Tested without any database — pure logic.
2. **Engine** (`app/engine/`) — `Rule` base class (reactive: `entity_key()` + `is_violating()` + `render_message()`) and `DurationRule` base class (tick-based: `watched_state()` + `is_too_long()`, checked on a timer via `Engine.tick()` instead of from an event). Built and proved out with the two most different rule shapes first: `QueueBacklogRule` (reactive) and `LongCallRule` (duration-based) — deliberately picked one of each so the pattern was proven twice, not just once, before building more.
3. **`RuleStateTracker`** — the no-repeat-alert mechanism. Only fires a notification on the ok→firing transition. Proven with tests that specifically check "stays firing → no repeat" and "recovers then breaches again → fires fresh."
4. **Persistence** (`app/persistence/`) — `rules` / `rule_state` / `notifications` tables, a `rule_type` → class registry (`app/engine/rules/__init__.py`), and a loader that turns a database row back into a live `Rule` object.
5. **Router** (`app/router/`) — persists a notification and hands it to a delivery function (defaults to printing to console, which is the stub delivery the prompt asks for).
6. **API** (`app/api/`) — FastAPI app. Full CRUD on rules (create/list/edit/delete), notifications (list/resolve/unresolve/delete), and a `POST /events` endpoint that feeds the live running engine. The app bootstraps its own database schema on startup (`Base.metadata.create_all`) so it works against a genuinely empty database with no separate migration step — appropriate for this scope, would be Alembic in a real production setup.
7. **The rule cache, for real this time** — `Engine.rules` is the in-memory cache we designed early on; a background poller (`app/api/rule_poller.py`) reloads it from Postgres every 5 seconds, so a rule created through the API takes effect without restarting the server. This was designed in the very first architecture conversation and only actually built once the API existed and made it necessary.
8. **Two demo scripts** — `scripts/demo_offline.py` (self-contained, builds its own engine, no server needed — good for a fast sanity check) and `scripts/demo_live.py` (a real HTTP client that replays `data/events.txt` against the actual running API and database, at a configurable pace via `--speed`, default 18x = ~5 real minutes). Kept both on purpose: one proves the core logic in isolation, the other proves the whole system integrated.
9. **Frontend** (`frontend/`) — Vite + React, no state library, no CSS framework, no router. Three panels: Active rules, Notifications, Resolved. A modal (triggered by a "+" button) handles both creating and editing a rule, reusing one `RuleForm` component in two modes. Colors and font pulled from Assembled's real marketing site (`#F8F7F3` background, `#222637` navy, `#00453D` teal, IBM Plex Sans) rather than invented — checked their actual site and product screenshots rather than guessing at "looks professional."

## Real bugs found by actually running the thing, not just writing tests

- **Missing `greenlet` dependency** — SQLAlchemy's async engine needs it; only surfaced when a test actually ran against a live database.
- **Event loop mismatch in tests** — the DB engine is created once at import time, but pytest was handing out a fresh event loop per test by default. Fixed with `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope = "session"` in `pyproject.toml`.
- **No schema bootstrap for a fresh database** — tests always created their own tables via fixtures, but nothing did that for a real run of the app until `main.py`'s lifespan was taught to call `create_all` on startup. Found by actually starting the server, not by the test suite.
- **A live-crash in the frontend** — the create-rule form's live description preview called `.join(", ")` on `scope.agent_ids` before it had been converted from a raw typed string into an array, which only happened at submit time. Typing in that field threw mid-render and blanked the whole page. Fixed by normalizing once, before both the preview and the submit path use it, instead of normalizing only at submit time.
- **Whitespace/formatting fragility in rule matching** — a rule created with `"billing "` (trailing space) or agent IDs typed as `"a_11 a_12"` (no comma) would silently never match anything, since matching was an exact string comparison. Fixed at the matching layer (`.strip()` on both sides in `QueueBacklogRule`/`LongCallRule`, so it's correct regardless of where the data came from) and at input time (the agent-IDs field now splits on comma or whitespace).
- **Negative numbers accepted** — nothing stopped a threshold or a duration from being negative, which makes no product sense (can't have -5 tickets waiting). Fixed at the API layer, not just the UI, since the UI can be bypassed via curl/Swagger: `severity` is now bounded 1–10 via Pydantic's `Field(ge=1, le=10)`, and a generic check rejects any negative number in a rule's `params`.

## The one real incident: running tests wiped live dev data

**What happened:** tests and the live dev/demo session were pointed at the exact same Postgres database. The test fixtures do a full `create_all` → yield → `drop_all` cycle around every test. Running the test suite while the user had manually created real rules through the running app caused `drop_all` to destroy that data — rules they'd typed by hand were permanently gone.

**Root cause:** `DATABASE_URL` had one default, used everywhere — tests, the dev server, the demo scripts — with nothing separating "data I'm experimenting with" from "data a test fixture is allowed to nuke."

**Fix:** tests now get their own database (`notifications_test`, a separate Postgres database inside the same container). `tests/conftest.py` sets `DATABASE_URL` via `os.environ.setdefault(...)` before anything imports `app.persistence.database` (env var has to be set before that module's import-time `create_async_engine()` call runs). This makes the mistake structurally impossible going forward, not just "be careful next time."

**Lesson for next time a shared resource like this comes up:** before running a destructive-by-design test suite (anything that drops/truncates tables), verify it's pointed at a database nobody is actively using for real work — don't assume based on how the fixture is scoped.

## Design decisions made or refined during implementation (not just at the start)

- **Severity is per-rule-instance, not fixed per rule type.** Originally planned as a fixed property of each rule class. Changed after direct feedback: different team leads will disagree on what's most urgent to them, so it's a value on the rule row (with a `default_severity` per type only used to pre-fill the creation form), not baked into code.
- **Deleting a rule keeps its notification history.** First version cascaded the delete (removing a rule also deleted its past notifications). Reconsidered: a notification's message/severity/recipient are already stored on the notification row itself, so it stays meaningful even after the rule that caused it is gone. `notifications.rule_id` is nullable with `ON DELETE SET NULL`; only `rule_state` (unused, no history value) cascades.
- **Resolve/unresolve workflow for notifications**, added after the core system was working: `resolved` boolean on notifications, a third UI panel ("Resolved") separate from the live feed, undo available (mark unresolved again) since a resolve can be a misclick, and delete available from both panels, not gated behind resolving first.
- **`rule_state` (the table meant to make the no-repeat-tracker survive a restart) was deliberately left unbuilt**, with the reasoning documented directly on the class in `app/persistence/models.py` rather than in a comment buried in this file — so a cold reader of the code sees the limitation exactly where it matters, not just in project notes.

## Current state (what's built vs. what's left)

**Built and working, verified live (not just by tests):** ingestor, engine (both reactive and duration-based rules), no-repeat-alert tracking, persistence, router, full rule CRUD via API, `/events` ingestion endpoint, the rule-cache poller, both demo scripts, and a complete frontend (create/edit/delete rules via modal, active/resolved notification panels with resolve/undo/delete, Assembled-derived visual design).

**Rule catalog:** only `queue_backlog` and `long_call` are actually implemented, out of the ~10 designed in the earlier section of this doc. Deliberately not built further — these two already prove both mechanical shapes the catalog needs (reactive vs. duration-based), and more rule types are additional instances of an already-proven pattern, not new design risk. Explainable as a scope cut, not a gap.

**Explicitly not built, and why:**
- `rule_state` persistence (see above) — named limitation, not an oversight.
- The rest of the rule catalog — same reasoning as above.
- Real Slack/email delivery — out of scope per the prompt; console + persisted notification log is the stub.
- Auth/multi-tenancy — out of scope per the prompt.

**Known rough edges, worth naming rather than hiding:**
- No automated frontend tests — verified manually via the browser tool throughout, but there's no equivalent of the backend's pytest suite for the UI.
- Params validation (`Field(ge=1, le=10)` for severity, a generic negative-number check for `params`) is a light guard, not exhaustive — e.g., nothing stops a `duration_min` of 0.5 or a wildly large threshold; good enough for this scope, not production-grade input validation.

