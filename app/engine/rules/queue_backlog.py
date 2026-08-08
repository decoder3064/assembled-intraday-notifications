from app.engine.rule import Rule
from app.ingestor.schemas import Event


class QueueBacklogRule(Rule):
    rule_type = "queue_backlog"
    default_severity = 4  # low — just a suggested default, user can override

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id != self.scope["queue_id"]:
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        return event.tickets_waiting > self.params["threshold"]

    def render_message(self, event: Event) -> str:
        return (
            f"{event.queue_id} has {event.tickets_waiting} tickets waiting "
            f"(threshold: {self.params['threshold']})"
        )
