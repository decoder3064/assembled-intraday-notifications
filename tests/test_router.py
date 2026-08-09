import uuid

from sqlalchemy import select

from app.engine.engine import Notification
from app.engine.rules.queue_backlog import QueueBacklogRule
from app.persistence.models import NotificationRow, RuleRow
from app.router.router import Router


async def _notification(db_session, message="billing has 25 tickets waiting"):
    """Persist a real RuleRow first, so the notification's rule_id satisfies
    the foreign key — a fabricated rule_id would (correctly) be rejected."""
    row = RuleRow(
        id=uuid.uuid4(), rule_type="queue_backlog", scope={"queue_id": "billing"},
        params={"threshold": 20}, recipient_id="lead_maria",
        description="Notify me when billing backs up past 20", severity=4,
    )
    db_session.add(row)
    await db_session.commit()

    rule = QueueBacklogRule(
        rule_id=str(row.id), scope=row.scope, params=row.params,
        recipient_id=row.recipient_id, severity=row.severity,
    )
    return Notification(rule, message)


async def test_dispatch_persists_notification_row(db_session):
    router = Router(session=db_session, delivery=lambda n: None)

    await router.dispatch(await _notification(db_session))

    result = await db_session.execute(select(NotificationRow))
    rows = result.scalars().all()

    assert len(rows) == 1
    assert rows[0].recipient_id == "lead_maria"
    assert rows[0].message == "billing has 25 tickets waiting"
    assert rows[0].severity == 4


async def test_dispatch_calls_delivery_with_the_notification(db_session):
    delivered = []
    router = Router(session=db_session, delivery=delivered.append)

    notification = await _notification(db_session)
    await router.dispatch(notification)

    assert delivered == [notification]
