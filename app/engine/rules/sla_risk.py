from app.engine.rule import Rule
from app.ingestor.schemas import Event


class SlaRiskRule(Rule):
    rule_type = "sla_risk"
    default_severity = 3  # low — an early warning, not yet a breach

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id.strip() != self.scope["queue_id"].strip():
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        threshold = event.sla_target_sec * self.params["pct_of_sla"]
        return threshold <= event.longest_wait_sec < event.sla_target_sec

    def render_message(self, event: Event) -> str:
        return (
            f"{event.queue_id} is nearing its SLA — waited {event.longest_wait_sec}s "
            f"of {event.sla_target_sec}s"
        )
