from app.engine.rule import Rule
from app.engine.rules.long_call import LongCallRule
from app.engine.rules.queue_backlog import QueueBacklogRule

RULE_REGISTRY: dict[str, type[Rule]] = {
    QueueBacklogRule.rule_type: QueueBacklogRule,
    LongCallRule.rule_type: LongCallRule,
}


class UnknownRuleType(ValueError):
    pass


def build_rule(rule_type: str, rule_id: str, scope: dict, params: dict, recipient_id: str, severity: int) -> Rule:
    rule_class = RULE_REGISTRY.get(rule_type)
    if rule_class is None:
        raise UnknownRuleType(f"unrecognized rule type: {rule_type!r}")
    return rule_class(rule_id=rule_id, scope=scope, params=params, recipient_id=recipient_id, severity=severity)
