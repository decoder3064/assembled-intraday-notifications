from app.util.duration import format_duration
from app.engine.rule import Rule
from app.ingestor.schemas import Event


class SlaRiskRule(Rule):
    rule_type = "sla_risk"

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id.strip() != self.scope["queue_id"].strip():
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        threshold = event.sla_target_sec * self.params["pct_of_sla"]
        return threshold <= event.longest_wait_sec < event.sla_target_sec

    def render_message(self, event: Event) -> str:
        remaining = format_duration(event.sla_target_sec - event.longest_wait_sec)
        limit = format_duration(event.sla_target_sec)
        return f"{event.queue_id}'s longest wait is {format_duration(event.longest_wait_sec)} now, {remaining} before it breaches the {limit} you promised customers"
