# Intraday Notification System — Design Spec

Assembled take-home. This is the formal reference for what's being built and why. The reasoning/narrative version, meant for the live walkthrough, lives in [`decisions.md`](../../../decisions.md) at the repo root — this doc is the thing the code should match.

## 1. Problem and scope

Build a system that watches a live stream of contact-center events (queue health, agent state, adherence) and notifies the right person when something needs attention — without becoming noise. Rule definitions ("notify me when X") are configured by end users, stored as data, and evaluated against incoming events in real time.

**Explicitly out of scope** (per the prompt): real Slack/email/push delivery (stubbed instead), auth/authz/multi-tenancy, production deploy/CI/CD/infra-as-code.

## 2. Audience

**Team leads** (primary) and **agents** (self-service, one use case). No head-of-support view.

- Team lead gets a command-center view: their queues' health plus individual detail on their agents (adherence, call length) — not a separate agent-facing screen, folded into the one dashboard.
- Agents get exactly one thing: a private nudge about their own adherence, before it escalates to their lead.
- Head of support is a different feature (a rolled-up digest, not a real-time alert) — deliberately cut, not built.

Rationale, alternatives considered, and the back-and-forth on this decision are in `decisions.md`.

## 3. Architecture

Three independent stages:

```
events → Ingestor → Engine → Router (dispatcher) → notification
                        ↑
                   Rules (Postgres, cached in-process)
```

- **Ingestor** — receives raw events, normalizes them, and guards against bad data (see §6).
- **Engine** — evaluates clean events against the current rules; also runs a periodic sweep (the "tick") for rules that depend on elapsed time rather than an incoming event.
- **Router** — decides who gets notified, renders the message, writes it to the notification log, and hands it to the (stubbed) delivery mechanism.

Rules live in Postgres, not in code, so a threshold change is a database edit, not a deploy. Each Engine process keeps its own in-memory copy of the rules, refreshed by polling every few seconds (see `decisions.md` for why polling was chosen over `LISTEN/NOTIFY`).

## 4. Data model

### `rules`
| column | type | notes |
|---|---|---|
| id | uuid | |
| rule_type | text | one of the 8 values in §5; validated in the application layer via a Python `Enum`, not a Postgres native enum, so adding a type later is a code change, not a migration |
| scope | jsonb | what the rule watches — `{"kind": "queue", "queue_id": "billing"}` or `{"kind": "agents", "agent_ids": [...]}`. Chosen explicitly by whoever creates the rule; there is no roster/org-chart lookup, since the event data doesn't provide one |
| params | jsonb | rule-type-specific thresholds, e.g. `{"threshold": 20}` |
| recipient_id | text | who gets notified — just a person id, not typed as "team lead" or "agent"; keeps the schema audience-agnostic |
| description | text | auto-rendered from a per-rule-type template at creation/edit time, not typed freely by the user |
| enabled | boolean | default true |
| created_at, updated_at | timestamp | |

### `rule_state`
Tracks whether a rule is *currently* firing, per entity it watches — this is what prevents re-notifying every 30 seconds while a condition remains true.

| column | type | notes |
|---|---|---|
| id | uuid | |
| rule_id | uuid → rules.id | |
| entity_key | text | the specific queue_id or agent_id this state row is about (a team-scoped rule has one row per agent it watches) |
| status | text | `ok` \| `firing` |
| fired_at | timestamp \| null | when the current firing period started |
| last_notified_at | timestamp \| null | |

### `notifications`
The output log — also what the `/notifications` view reads from.

| column | type | notes |
|---|---|---|
| id | uuid | |
| rule_id | uuid → rules.id | |
| recipient_id | text | |
| message | text | rendered from the rule type's message template + the triggering event's live data |
| severity | int | fixed per rule_type (see §5), used to sort the feed |
| sent_at | timestamp | |

## 5. Rule catalog

Exactly 8 known rule types — a fixed catalog, not a general expression language (an open-ended condition string or NLP input was considered and rejected; see `decisions.md`). Each is implemented as a subclass of a base `Rule` class with `evaluate(event, params) -> bool`, `render_message(event) -> str`, and a fixed `severity`.

| rule_type | recipient | reads | severity |
|---|---|---|---|
| `queue_backlog` | team lead | `queue_snapshot.tickets_waiting` | low |
| `sla_risk` | team lead | `queue_snapshot.longest_wait_sec` vs `sla_target_sec × pct_of_sla` | low |
| `sla_breach` | team lead | `longest_wait_sec` ≥ `sla_target_sec` | 2nd highest |
| `volume_surge` | team lead | `volume_last_15m` vs `volume_forecast_next_15m` | 3rd |
| `long_call` | team lead | agent state duration, via the tick (see §6) | — |
| `adherence_self` | the agent themselves | `adherence_check.in_violation` / `violation_started_at`, short threshold (~10 min) | n/a — never shares a feed with the others |
| `adherence_escalated` | team lead | same underlying violation as above, longer threshold (~25 min) | highest |
| `zero_coverage` *(optional)* | team lead | `agents_available == 0` while `tickets_waiting > 0` | — |

Exact severity ordering is a product judgment call made and owned during design discussion — see `decisions.md` if it needs to be re-justified live.

## 6. Ingestor: handling real-world messiness

Confirmed with a script against the actual sample data (`data/events.txt`), not assumed:

1. **Duplicate events** — `evt_01HXYZ050` appears twice. Fix: track processed `event_id`s, drop repeats (idempotency).
2. **Out-of-order arrival** — a later event can have an *older* timestamp than the one before it, and this isn't only true of duplicates (`evt_01HXYZ096` is a unique event that still arrives "in the past" relative to what came before it). Fix: when updating current state for an agent or queue, compare the event's own timestamp to what's already stored, and discard the update if it's older — never trust arrival order. Late events are still written to the raw log, just not allowed to overwrite current state.
3. **Inconsistent null shapes** — `queue_ids` appears as both `null` and `[]` for "no queue." Normalized to one shape on the way in.
4. **Missing fields** — `volume_forecast_next_15m` can be `null`. Any rule reading it treats absence as "skip," not zero or a crash.
5. **Malformed events** — validated against a Pydantic model per event type at the ingestion boundary; a bad event is rejected there, not allowed to reach the engine.

**Known, deliberate limitation:** a late-arriving event is always blocked from overwriting current state, even if nothing newer has actually superseded it — i.e. "late" is treated as "ignore for live state" across the board, not "ignore only if something newer already contradicts it." The stricter, more complete version would ask "has something more recent already told me this isn't the situation anymore?" before discarding. Out of scope here — flagged as a named future improvement, not missed.

## 7. Engine: the tick

Some rules (`long_call`, and the adherence escalation window) are true only because time has passed with no new event — `agent_state_change` only fires when a call *ends*, reporting the *previous* state's duration, so nothing tells the engine a call is still running. The Engine therefore has two entry points, not one:

- `on_event(event)` — reactive path, runs on every incoming event.
- `tick()` — runs on a background loop (started at app boot, sleeps N seconds, repeats), sweeps every agent's `entered_state_at` (updated on every `agent_state_change`), and re-checks duration-based rules against the current time.

## 8. Testing strategy

Testing pyramid: mostly fast unit tests, few integration tests, one true end-to-end test.

- **Unit (no DB):** each `Rule` subclass's `evaluate()`; the idempotency check; the timestamp guard; the no-repeat-alert transition logic in `rule_state`.
- **Integration (real test DB):** the thin persistence layer — saving/loading rules, writing notifications.
- **End-to-end (golden test):** seed the 8 rules from §5, run the actual `data/events.txt` through the full pipeline, assert on the exact set of notifications produced.
- **Optional, time-permitting:** property-based/fuzz testing (e.g. Hypothesis) generating randomized malformed/duplicate/out-of-order event streams against the ingestor, beyond the two hand-found cases.

## 9. Explicitly deferred / open

- **Demo replay pacing** — whether `data/events.txt` replays at (compressed) real timestamps or steps through manually for the live walkthrough. Not yet decided; to be resolved during implementation rather than blocking design.
- **`LISTEN/NOTIFY` push-based cache invalidation** — named as a production improvement, not built (see `decisions.md` for the full reasoning on why polling was chosen).
- **The softer "late but still relevant" alerting check** described in §6.
- **Head-of-support digest view** — named cut, not built.

## 10. Stack

FastAPI (backend/API), Postgres (storage), React (small rule-management + notification-feed frontend — list and a create/edit form only, no auth, no drag-and-drop builder), pytest (testing).
