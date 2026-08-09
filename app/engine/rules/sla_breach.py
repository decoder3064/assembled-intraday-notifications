from app.util.duration import format_duration
from app.engine.rule import Rule
from app.ingestor.schemas import Event


class SlaBreachRule(Rule):
    rule_type = "sla_breach"

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id.strip() != self.scope["queue_id"].strip():
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        return event.longest_wait_sec >= event.sla_target_sec

    def render_message(self, event: Event) -> str:
        return f"Someone waited {format_duration(event.longest_wait_sec)} in {event.queue_id}, longer than the {format_duration(event.sla_target_sec)} you promised customers"
