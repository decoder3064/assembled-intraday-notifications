# Known limitations

Personal reference, not a deliverable — a straight list of where this system is genuinely limited, so nothing surprises you in the interview. Each one is reasoned through in `decisions.md`; this is just the flat list.

## Data trust
- **No way to verify incoming numbers are accurate.** `agents_on_call`, `agents_available`, `tickets_waiting`, etc. are trusted at face value from whatever sends them. If the upstream source is wrong, every rule built on top of it is wrong too, silently.
- **"Off schedule" is entirely upstream-defined.** The engine doesn't decide what counts as an adherence violation — it just reacts to the `in_violation` flag already set on the incoming event. Bad upstream logic there is invisible to this system.
- **Occupancy's denominator can undercount.** `agents_on_call / (agents_on_call + agents_available)` only knows about agents the current snapshot happens to mention — someone on an unlogged break is invisible to it, not counted as "not busy." Tried fixing this with a cross-checked roster, reverted it (see `decisions.md`) — the real fix is a second authoritative data source (a WFM/scheduling system), not something this layer can self-correct.
  - **Real example from the sample data, not hypothetical:** the 9:50am billing snapshot reports `agents_available: 0, agents_on_call: 3` → "100% occupancy." At that same moment, `a_19` (who also works billing) had been on an unscheduled break since 9:35 and stayed there — confirmed by three separate records. She's not counted as busy or free; she's just absent from the "3" entirely. The other three (`a_07`, `a_31`, `a_42`) really were on calls around then, so the number itself isn't "wrong," it's just incomplete: "100%" describes 3 of the 4 people who actually work billing, not the whole team.
  - **Confirmed by reading the code, not assumed:** `occupancy.py` never inspects any individual agent or their queue tags — it takes `agents_on_call`/`agents_available` directly off the one `queue_snapshot` line and divides. Nothing in this system cross-references "is this specific person on a call, and do they work this queue" to build that number; that computation already happened upstream, before we ever see it. Decision: that's correctly out of scope for this system — verifying upstream headcount is a different system's job (the actual phone/ACD platform, or a workforce-management tool), not something a downstream alerting layer should try to re-derive. Kept `occupancy` as-is, no cross-referencing added.

## Persistence & reliability
- **No-repeat-alert state is in-memory only.** A server restart can cause one duplicate notification for whatever was already firing at that moment (`rule_state` table exists but isn't wired up).
- **Duplicate-event protection resets on restart.** Re-running `demo_live.py` against a server that already saw those event IDs silently produces zero notifications (`200 OK`, empty array) until the server restarts.
- **No database migrations.** Schema is `Base.metadata.create_all` only (additive, create-if-missing). Adding a column later means a manual `ALTER TABLE`, not a real migration. Fine at this scale; would need Alembic in production.
- **`team_adherence_capacity`'s cross-refresh memory fix is rule-specific, not general.** A future rule with similar state needs its own hook; the more general "diff the poller" fix was considered and deliberately not built.

## Scope
- **Single team, hardcoded.** `KNOWN_QUEUES`/`KNOWN_AGENTS` are fixed lists matching one team's sample data. "Your whole team" phrasing and the single hardcoded recipient (`lead_maria`) would be wrong against a real multi-team org.
- **No auth, no multi-tenancy.** One implicit recipient, no login.
- **`recipient_id` still exists end-to-end but isn't user-facing.** Column, model field, and delivery logic are all still there; only the API stopped accepting it from a client. Bringing back multi-recipient support is cheap; the removal wasn't a real architectural change.

## Demo-specific
- **`volume_surge` can't be proven with the real sample data.** Actual call volume never once exceeds forecast anywhere in the whole file — the rule is correctly implemented, just unprovable without a synthetic test event.
- **Late-arriving events are only partly handled.** Never let old data overwrite something newer — that part's solid. Whether stale-but-still-useful late data should fire an alert at all isn't handled; it only showed up once in the sample data.

## Delivery & noise
- **No real Slack/email delivery** — console print + persisted row is the stub, per the prompt's scope.
- **No notification grouping/batching.** Multiple rules firing on the same queue within seconds of each other send separate notifications (and would send separate Slack messages in a real deployment). Discussed, deliberately not built — batching before dispatch is real scope (delay-vs-noise tradeoff, where the batch state lives), not a quick add.

## Validation & testing
- **Params validation is light.** Severity is bounded, negative numbers rejected — but nothing stops a `duration_min` of 0.5 or an absurdly large threshold.
- **Frontend test coverage is targeted, not exhaustive.** Covers the two real bugs found (agent-ID crash, percent-field conversion) plus tier logic — not full component coverage the way the backend suite covers the engine.
