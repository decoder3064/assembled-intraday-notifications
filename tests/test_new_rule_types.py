from app.engine.engine import Engine
from app.engine.rules.adherence_escalated import AdherenceEscalatedRule
from app.engine.rules.occupancy import OccupancyRule
from app.engine.rules.sla_breach import SlaBreachRule
from app.engine.rules.sla_risk import SlaRiskRule
from app.engine.rules.team_adherence_capacity import TeamAdherenceCapacityRule
from app.engine.rules.volume_surge import VolumeSurgeRule
from app.engine.rules.zero_coverage import ZeroCoverageRule
from app.ingestor.ingestor import Ingestor


def _snapshot(event_id, **overrides):
    base = {
        "event_id": event_id, "ts": "2026-05-26T09:15:00Z", "type": "queue_snapshot",
        "queue_id": "billing", "tickets_waiting": 5, "longest_wait_sec": 30,
        "sla_target_sec": 120, "agents_available": 2, "agents_on_call": 3,
        "volume_last_15m": 15, "volume_forecast_next_15m": 20,
    }
    base.update(overrides)
    return base


def _adherence(event_id, agent_id, **overrides):
    base = {
        "event_id": event_id, "ts": "2026-05-26T09:15:00Z", "type": "adherence_check",
        "agent_id": agent_id, "queue_ids": ["billing"], "scheduled_state": "available",
        "actual_state": "on_break", "in_violation": True,
        "violation_started_at": "2026-05-26T09:00:00Z",  # 15 min before ts
    }
    base.update(overrides)
    return base


def test_sla_risk_fires_before_breach_not_after():
    ingestor = Ingestor()
    rule = SlaRiskRule(rule_id="r", scope={"queue_id": "billing"}, params={"pct_of_sla": 0.8}, recipient_id="lead", severity=3)
    engine = Engine(rules=[rule])

    # 100s of 120s target = 83%, past the 80% risk line but not yet breached
    event = ingestor.process(_snapshot("e1", longest_wait_sec=100))
    assert len(engine.on_event(event)) == 1


def test_sla_risk_does_not_fire_once_actually_breached():
    ingestor = Ingestor()
    rule = SlaRiskRule(rule_id="r", scope={"queue_id": "billing"}, params={"pct_of_sla": 0.8}, recipient_id="lead", severity=3)
    engine = Engine(rules=[rule])

    event = ingestor.process(_snapshot("e1", longest_wait_sec=150))  # already past 120s target
    assert engine.on_event(event) == []


def test_sla_breach_fires_at_or_past_target():
    ingestor = Ingestor()
    rule = SlaBreachRule(rule_id="r", scope={"queue_id": "billing"}, params={}, recipient_id="lead", severity=9)
    engine = Engine(rules=[rule])

    event = ingestor.process(_snapshot("e1", longest_wait_sec=130))
    assert len(engine.on_event(event)) == 1


def test_volume_surge_skips_when_forecast_missing():
    ingestor = Ingestor()
    rule = VolumeSurgeRule(rule_id="r", scope={"queue_id": "billing"}, params={"pct_over_forecast": 0.5}, recipient_id="lead", severity=6)
    engine = Engine(rules=[rule])

    event = ingestor.process(_snapshot("e1", volume_last_15m=100, volume_forecast_next_15m=None))
    assert engine.on_event(event) == []  # must not treat missing forecast as 0


def test_volume_surge_fires_when_real_traffic_exceeds_forecast():
    ingestor = Ingestor()
    rule = VolumeSurgeRule(rule_id="r", scope={"queue_id": "billing"}, params={"pct_over_forecast": 0.5}, recipient_id="lead", severity=6)
    engine = Engine(rules=[rule])

    event = ingestor.process(_snapshot("e1", volume_last_15m=100, volume_forecast_next_15m=20))
    assert len(engine.on_event(event)) == 1


def test_zero_coverage_requires_both_no_agents_and_waiting_tickets():
    ingestor = Ingestor()
    rule = ZeroCoverageRule(rule_id="r", scope={"queue_id": "billing"}, params={}, recipient_id="lead", severity=10)
    engine = Engine(rules=[rule])

    assert engine.on_event(ingestor.process(_snapshot("e1", agents_available=0, tickets_waiting=0))) == []
    assert len(engine.on_event(ingestor.process(_snapshot("e2", agents_available=0, tickets_waiting=3)))) == 1


def test_occupancy_fires_past_threshold():
    ingestor = Ingestor()
    rule = OccupancyRule(rule_id="r", scope={"queue_id": "billing"}, params={"occupancy_threshold": 0.8}, recipient_id="lead", severity=5)
    engine = Engine(rules=[rule])

    # 9 on call, 1 available = 90% occupancy
    event = ingestor.process(_snapshot("e1", agents_on_call=9, agents_available=1))
    assert len(engine.on_event(event)) == 1


def test_adherence_escalated_scoped_to_team_not_just_one_agent():
    ingestor = Ingestor()
    rule = AdherenceEscalatedRule(
        rule_id="r", scope={"agent_ids": ["a_19", "a_31"]}, params={"duration_min": 10},
        recipient_id="lead_maria", severity=9,
    )
    engine = Engine(rules=[rule])

    assert len(engine.on_event(ingestor.process(_adherence("e1", "a_31")))) == 1
    assert engine.on_event(ingestor.process(_adherence("e2", "a_88"))) == []  # not in scope


def test_team_adherence_capacity_counts_across_multiple_events():
    ingestor = Ingestor()
    rule = TeamAdherenceCapacityRule(
        rule_id="r", scope={"agent_ids": ["a_19", "a_31", "a_88"]}, params={"count_threshold": 1},
        recipient_id="lead_maria", severity=8,
    )
    engine = Engine(rules=[rule])

    # first violating agent: 1 violating, threshold is ">1", so no fire yet
    assert engine.on_event(ingestor.process(_adherence("e1", "a_19"))) == []
    # second violating agent: now 2 violating, crosses the threshold
    notifications = engine.on_event(ingestor.process(_adherence("e2", "a_31")))
    assert len(notifications) == 1
    assert "2 of your agents" in notifications[0].message


def test_team_adherence_capacity_ignores_a_late_arriving_stale_event():
    ingestor = Ingestor()
    rule = TeamAdherenceCapacityRule(
        rule_id="r", scope={"agent_ids": ["a_19", "a_31"]}, params={"count_threshold": 0},
        recipient_id="lead_maria", severity=8,
    )
    engine = Engine(rules=[rule])

    # A newer event says a_19 is in violation.
    engine.on_event(ingestor.process(_adherence("e1", "a_19", ts="2026-05-26T09:45:00Z")))
    assert "a_19" in rule._violating_agents

    # A late-arriving event, older than the one already processed, says
    # a_19 was fine — it must not undo the newer, still-true violation.
    engine.on_event(
        ingestor.process(_adherence("e2", "a_19", ts="2026-05-26T09:15:00Z", in_violation=False, violation_started_at=None))
    )
    assert "a_19" in rule._violating_agents


def test_team_adherence_capacity_carry_over_keeps_a_whitespace_padded_agent_id():
    ingestor = Ingestor()
    rule = TeamAdherenceCapacityRule(
        rule_id="r", scope={"agent_ids": ["a_19"]}, params={"count_threshold": 0},
        recipient_id="lead_maria", severity=8,
    )
    engine = Engine(rules=[rule])

    # The incoming event's agent_id has incidental whitespace.
    engine.on_event(ingestor.process(_adherence("e1", " a_19")))
    assert "a_19" in rule._violating_agents

    # Simulate a rule-cache refresh (the poller, or an unrelated rule delete).
    fresh_rule = TeamAdherenceCapacityRule(
        rule_id="r", scope={"agent_ids": ["a_19"]}, params={"count_threshold": 0},
        recipient_id="lead_maria", severity=8,
    )
    engine.set_rules([fresh_rule])

    # Must survive the refresh, not get silently dropped by a stripped-vs-raw
    # key mismatch between the carried-over state and the new scope.
    assert engine.rules[0]._violating_agents == {"a_19"}


def test_team_adherence_capacity_tally_survives_a_rule_cache_refresh():
    ingestor = Ingestor()
    rule = TeamAdherenceCapacityRule(
        rule_id="r", scope={"agent_ids": ["a_19", "a_31", "a_88"]}, params={"count_threshold": 1},
        recipient_id="lead_maria", severity=8,
    )
    engine = Engine(rules=[rule])

    engine.on_event(ingestor.process(_adherence("e1", "a_19")))
    engine.on_event(ingestor.process(_adherence("e2", "a_31")))  # 2 violating, already fired once

    # simulate the poller: a brand new rule object, same rule_id, no memory of its own
    fresh_rule = TeamAdherenceCapacityRule(
        rule_id="r", scope={"agent_ids": ["a_19", "a_31", "a_88"]}, params={"count_threshold": 1},
        recipient_id="lead_maria", severity=8,
    )
    assert fresh_rule._violating_agents == set()  # confirms it really starts empty
    engine.set_rules([fresh_rule])

    # without carry_over_state, this would be undercounted (2 not 3) since the
    # fresh object never saw a_19/a_31's original events
    notifications = engine.on_event(ingestor.process(_adherence("e3", "a_88")))
    assert engine.rules[0]._violating_agents == {"a_19", "a_31", "a_88"}
    assert notifications == []  # still "firing" from before, not a fresh transition
