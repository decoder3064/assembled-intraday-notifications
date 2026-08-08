from app.engine.rules import build_rule
from app.persistence.models import RuleRow


def rule_from_row(row: RuleRow):
    return build_rule(
        rule_type=row.rule_type,
        rule_id=str(row.id),
        scope=row.scope,
        params=row.params,
        recipient_id=row.recipient_id,
        severity=row.severity,
    )
