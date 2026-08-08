from app.engine.engine import Engine
from app.engine.rules.queue_backlog import QueueBacklogRule
from app.ingestor.ingestor import Ingestor


def _snapshot(event_id, tickets_waiting, queue_id="billing"):
    return {
        "event_id": event_id, "ts": "2026-05-26T09:15:00Z", "type": "queue_snapshot",
        "queue_id": queue_id, "tickets_waiting": tickets_waiting, "longest_wait_sec": 90,
        "sla_target_sec": 120, "agents_available": 2, "agents_on_call": 3,
        "volume_last_15m": 15, "volume_forecast_next_15m": 20,
    }


def _rule(threshold=20):
    return QueueBacklogRule(
        rule_id="rule_1", scope={"queue_id": "billing"}, params={"threshold": threshold},
        recipient_id="lead_maria", severity=4,
    )


def test_crossing_threshold_fires_one_notification():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(threshold=20)])

    event = ingestor.process(_snapshot("evt_1", tickets_waiting=25))
    notifications = engine.on_event(event)

    assert len(notifications) == 1
    assert notifications[0].recipient_id == "lead_maria"
    assert "25 tickets waiting" in notifications[0].message


def test_staying_over_threshold_does_not_repeat():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(threshold=20)])

    engine.on_event(ingestor.process(_snapshot("evt_1", tickets_waiting=25)))
    notifications = engine.on_event(ingestor.process(_snapshot("evt_2", tickets_waiting=30)))

    assert notifications == []


def test_recovering_then_breaching_again_fires_a_fresh_notification():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(threshold=20)])

    engine.on_event(ingestor.process(_snapshot("evt_1", tickets_waiting=25)))
    engine.on_event(ingestor.process(_snapshot("evt_2", tickets_waiting=5)))  # recovers
    notifications = engine.on_event(ingestor.process(_snapshot("evt_3", tickets_waiting=30)))  # breaches again

    assert len(notifications) == 1


def test_event_for_a_different_queue_is_ignored():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(threshold=20)])

    event = ingestor.process(_snapshot("evt_1", tickets_waiting=99, queue_id="tier_2"))
    notifications = engine.on_event(event)

    assert notifications == []


def test_below_threshold_never_fires():
    ingestor = Ingestor()
    engine = Engine(rules=[_rule(threshold=20)])

    event = ingestor.process(_snapshot("evt_1", tickets_waiting=5))
    notifications = engine.on_event(event)

    assert notifications == []


def test_set_rules_replaces_the_active_rule_list():
    rule_a = QueueBacklogRule(
        rule_id="a", scope={"queue_id": "billing"}, params={"threshold": 20},
        recipient_id="lead_maria", severity=4,
    )
    rule_b = QueueBacklogRule(
        rule_id="b", scope={"queue_id": "tier_2"}, params={"threshold": 5},
        recipient_id="lead_maria", severity=4,
    )

    engine = Engine(rules=[rule_a])
    assert engine.rules == [rule_a]

    engine.set_rules([rule_b])
    assert engine.rules == [rule_b]


def test_no_repeat_alert_survives_a_rule_refresh_with_the_same_rule_id():
    """A poll-refresh builds brand new Rule objects from the database every
    cycle. Since RuleStateTracker keys on rule_id (not object identity), a
    rule that's already firing shouldn't re-notify just because the object
    representing it got swapped out for a fresh one with the same id."""
    ingestor = Ingestor()
    rule_v1 = _rule(threshold=20)
    engine = Engine(rules=[rule_v1])

    notifications = engine.on_event(ingestor.process(_snapshot("evt_1", tickets_waiting=25)))
    assert len(notifications) == 1  # first breach, fires

    rule_v2 = _rule(threshold=20)  # a different object, same rule_id
    engine.set_rules([rule_v2])

    notifications = engine.on_event(ingestor.process(_snapshot("evt_2", tickets_waiting=30)))
    assert notifications == []  # still firing, no repeat, despite the object swap
