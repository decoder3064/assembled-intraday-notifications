import uuid

from app.engine.engine import Notification
from app.persistence.models import NotificationRow


def console_delivery(notification: Notification) -> None:
    print(f"[notify:{notification.recipient_id}] (severity {notification.severity}) {notification.message}")


class Router:
    def __init__(self, session, delivery=console_delivery):
        self.session = session
        self.delivery = delivery

    async def dispatch(self, notification: Notification) -> None:
        row = NotificationRow(
            rule_id=uuid.UUID(notification.rule_id),
            rule_type=notification.rule_type,
            recipient_id=notification.recipient_id,
            message=notification.message,
            severity=notification.severity,
        )
        self.session.add(row)
        await self.session.commit()
        self.delivery(notification)
