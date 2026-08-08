import pytest

from app.engine.rules import UnknownRuleType, build_rule
from app.engine.rules.long_call import LongCallRule
from app.engine.rules.queue_backlog import QueueBacklogRule


def test_build_known_rule_type_returns_correct_class():
    rule = build_rule(
        rule_type="queue_backlog", rule_id="r1", scope={"queue_id": "billing"},
        params={"threshold": 20}, recipient_id="lead_maria", severity=4,
    )
    assert isinstance(rule, QueueBacklogRule)
    assert rule.rule_id == "r1"
    assert rule.params["threshold"] == 20


def test_build_another_known_rule_type():
    rule = build_rule(
        rule_type="long_call", rule_id="r2", scope={"agent_ids": ["a_19"]},
        params={"duration_min": 45}, recipient_id="lead_maria", severity=6,
    )
    assert isinstance(rule, LongCallRule)


def test_build_unknown_rule_type_raises():
    with pytest.raises(UnknownRuleType):
        build_rule(
            rule_type="does_not_exist", rule_id="r3", scope={}, params={},
            recipient_id="lead_maria", severity=1,
        )
