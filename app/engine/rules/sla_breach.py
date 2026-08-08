from app.engine.rule import Rule
from app.ingestor.schemas import Event


class SlaBreachRule(Rule):
    rule_type = "sla_breach"
    default_severity = 9  # high — the deadline's already missed

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id.strip() != self.scope["queue_id"].strip():
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        return event.longest_wait_sec >= event.sla_target_sec

    def render_message(self, event: Event) -> str:
        return (
            f"{event.queue_id} has breached its SLA — waited {event.longest_wait_sec}s "
            f"(limit: {event.sla_target_sec}s)"
        )
