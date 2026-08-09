from app.engine.rule import Rule
from app.ingestor.schemas import Event


class OccupancyRule(Rule):
    rule_type = "occupancy"

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id.strip() != self.scope["queue_id"].strip():
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        total = event.agents_on_call + event.agents_available
        if total == 0:
            return False
        return (event.agents_on_call / total) > self.params["occupancy_threshold"]

    def render_message(self, event: Event) -> str:
        total = event.agents_on_call + event.agents_available
        pct = round(100 * event.agents_on_call / total) if total else 0
        return f"{event.queue_id} occupancy is at {pct}%: {event.agents_on_call} of {total} agents are on calls"
