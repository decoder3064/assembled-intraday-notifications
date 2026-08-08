from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.rule import Rule
from app.engine.rules import build_rule
from app.persistence.models import RuleRow


def rule_from_row(row: RuleRow) -> Rule:
    return build_rule(
        rule_type=row.rule_type,
        rule_id=str(row.id),
        scope=row.scope,
        params=row.params,
        recipient_id=row.recipient_id,
        severity=row.severity,
    )


async def load_enabled_rules(session: AsyncSession) -> list[Rule]:
    result = await session.execute(select(RuleRow).where(RuleRow.enabled.is_(True)))
    return [rule_from_row(row) for row in result.scalars().all()]
