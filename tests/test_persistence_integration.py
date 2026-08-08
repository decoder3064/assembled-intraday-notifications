import uuid

from sqlalchemy import select

from app.engine.rules.queue_backlog import QueueBacklogRule
from app.persistence.loader import rule_from_row
from app.persistence.models import RuleRow


async def test_saved_rule_can_be_loaded_back_as_the_right_rule_object(db_session):
    row = RuleRow(
        id=uuid.uuid4(),
        rule_type="queue_backlog",
        scope={"queue_id": "billing"},
        params={"threshold": 20},
        recipient_id="lead_maria",
        description="Notify me when billing backs up past 20",
        severity=4,
    )
    db_session.add(row)
    await db_session.commit()

    result = await db_session.execute(select(RuleRow).where(RuleRow.id == row.id))
    loaded_row = result.scalar_one()

    rule = rule_from_row(loaded_row)

    assert isinstance(rule, QueueBacklogRule)
    assert rule.params["threshold"] == 20
    assert rule.recipient_id == "lead_maria"
