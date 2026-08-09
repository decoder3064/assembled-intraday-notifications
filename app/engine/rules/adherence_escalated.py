from app.util.agent_names import format_agent_name
from app.util.duration import format_duration
from app.engine.rule import Rule
from app.ingestor.schemas import Event


class AdherenceEscalatedRule(Rule):
    """Same underlying violation type as a self-nudge would check, but a longer threshold
    and the team lead as recipient — for when it's stopped being 'forgot to
    switch a toggle' and become something the team needs to react to."""

    rule_type = "adherence_escalated"

    def entity_key(self, event: Event) -> str | None:
        if event.type != "adherence_check" or event.agent_id.strip() not in {
            a.strip() for a in self.scope["agent_ids"]
        }:
            return None
        return event.agent_id

    def is_violating(self, event: Event) -> bool:
        if not event.in_violation or event.violation_started_at is None:
            return False
        duration = (event.ts - event.violation_started_at).total_seconds()
        return duration > self.params["duration_min"] * 60

    def render_message(self, event: Event) -> str:
        elapsed = (event.ts - event.violation_started_at).total_seconds()
        threshold_sec = self.params["duration_min"] * 60
        overage = format_duration(elapsed - threshold_sec)
        return (
            f"{format_agent_name(event.agent_id)} has been off schedule for {format_duration(elapsed)} now, "
            f"{overage} past your {format_duration(threshold_sec)} limit"
        )
