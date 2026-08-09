from app.engine.rule import Rule
from app.ingestor.schemas import Event


class ZeroCoverageRule(Rule):
    rule_type = "zero_coverage"

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id.strip() != self.scope["queue_id"].strip():
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        return event.agents_available == 0 and event.tickets_waiting > 0

    def render_message(self, event: Event) -> str:
        return f"{event.queue_id} has 0 agents available with {event.tickets_waiting} tickets waiting"
