from datetime import datetime, timezone

from app.engine.engine import Engine
from app.engine.rules.long_call import LongCallRule
from app.ingestor.ingestor import Ingestor


def _state_change(event_id, agent_id, new_state, ts, previous_state="available"):
    return {
        "event_id": event_id, "ts": ts, "type": "agent_state_change",
        "agent_id": agent_id, "queue_ids": ["billing"], "previous_state": previous_state,
        "previous_state_duration_sec": 300, "new_state": new_state,
    }


def _rule(duration_min=45, agent_ids=("a_19",)):
    return LongCallRule(
        rule_id="rule_lc", scope={"agent_ids": list(agent_ids)}, params={"duration_min": duration_min},
        recipient_id="lead_maria", severity=6,
    )


def test_tick_before_threshold_does_not_fire():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(duration_min=45)])

    engine.on_event(ingestor.process(_state_change("evt_1", "a_19", "on_call", "2026-05-26T09:00:00Z")))

    now = datetime(2026, 5, 26, 9, 30, 0, tzinfo=timezone.utc)  # 30 min in, under the 45 min threshold
    assert engine.tick(now) == []


def test_tick_after_threshold_fires_once():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(duration_min=45)])

    engine.on_event(ingestor.process(_state_change("evt_1", "a_19", "on_call", "2026-05-26T09:00:00Z")))

    now = datetime(2026, 5, 26, 9, 50, 0, tzinfo=timezone.utc)  # 50 min in, over the threshold
    notifications = engine.tick(now)

    assert len(notifications) == 1
    assert notifications[0].recipient_id == "lead_maria"
    assert "a_19" in notifications[0].message


def test_repeated_ticks_while_still_on_the_call_do_not_repeat():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(duration_min=45)])

    engine.on_event(ingestor.process(_state_change("evt_1", "a_19", "on_call", "2026-05-26T09:00:00Z")))

    engine.tick(datetime(2026, 5, 26, 9, 50, 0, tzinfo=timezone.utc))
    notifications = engine.tick(datetime(2026, 5, 26, 10, 0, 0, tzinfo=timezone.utc))

    assert notifications == []


def test_call_ending_resets_the_tracked_state():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(duration_min=45)])

    engine.on_event(ingestor.process(_state_change("evt_1", "a_19", "on_call", "2026-05-26T09:00:00Z")))
    engine.on_event(ingestor.process(
        _state_change("evt_2", "a_19", "available", "2026-05-26T09:50:00Z", previous_state="on_call")
    ))

    now = datetime(2026, 5, 26, 10, 0, 0, tzinfo=timezone.utc)
    assert engine.tick(now) == []


def test_agent_outside_scope_never_fires():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(duration_min=45, agent_ids=("a_31",))])  # rule only watches a_31

    engine.on_event(ingestor.process(_state_change("evt_1", "a_19", "on_call", "2026-05-26T09:00:00Z")))

    now = datetime(2026, 5, 26, 10, 0, 0, tzinfo=timezone.utc)
    assert engine.tick(now) == []
