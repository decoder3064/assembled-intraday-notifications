from app.engine.rule import Rule
from app.engine.rules.adherence_escalated import AdherenceEscalatedRule
from app.engine.rules.adherence_self import AdherenceSelfRule
from app.engine.rules.long_call import LongCallRule
from app.engine.rules.occupancy import OccupancyRule
from app.engine.rules.queue_backlog import QueueBacklogRule
from app.engine.rules.sla_breach import SlaBreachRule
from app.engine.rules.sla_risk import SlaRiskRule
from app.engine.rules.team_adherence_capacity import TeamAdherenceCapacityRule
from app.engine.rules.volume_surge import VolumeSurgeRule
from app.engine.rules.zero_coverage import ZeroCoverageRule

RULE_REGISTRY: dict[str, type[Rule]] = {
    QueueBacklogRule.rule_type: QueueBacklogRule,
    LongCallRule.rule_type: LongCallRule,
    SlaRiskRule.rule_type: SlaRiskRule,
    SlaBreachRule.rule_type: SlaBreachRule,
    VolumeSurgeRule.rule_type: VolumeSurgeRule,
    ZeroCoverageRule.rule_type: ZeroCoverageRule,
    AdherenceSelfRule.rule_type: AdherenceSelfRule,
    AdherenceEscalatedRule.rule_type: AdherenceEscalatedRule,
    TeamAdherenceCapacityRule.rule_type: TeamAdherenceCapacityRule,
    OccupancyRule.rule_type: OccupancyRule,
}


class UnknownRuleType(ValueError):
    pass


def build_rule(rule_type: str, rule_id: str, scope: dict, params: dict, recipient_id: str, severity: int) -> Rule:
    rule_class = RULE_REGISTRY.get(rule_type)
    if rule_class is None:
        raise UnknownRuleType(f"unrecognized rule type: {rule_type!r}")
    return rule_class(rule_id=rule_id, scope=scope, params=params, recipient_id=recipient_id, severity=severity)
