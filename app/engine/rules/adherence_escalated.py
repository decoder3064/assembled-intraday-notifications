from app.engine.rule import Rule
from app.ingestor.schemas import Event


class AdherenceEscalatedRule(Rule):
    """Same underlying violation as adherence_self, but a longer threshold
    and the team lead as recipient — for when it's stopped being 'forgot to
    switch a toggle' and become something the team needs to react to."""

    rule_type = "adherence_escalated"
    default_severity = 9

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
        return f"{event.agent_id} has been off-schedule for a while and hasn't fixed it"
