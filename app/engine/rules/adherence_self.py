from app.engine.rule import Rule
from app.ingestor.schemas import Event


class AdherenceSelfRule(Rule):
    """Private nudge to the agent themselves — short threshold, never
    shares a feed with anyone else's rules."""

    rule_type = "adherence_self"
    default_severity = 2

    def entity_key(self, event: Event) -> str | None:
        if event.type != "adherence_check" or event.agent_id.strip() != self.scope["agent_id"].strip():
            return None
        return event.agent_id

    def is_violating(self, event: Event) -> bool:
        if not event.in_violation or event.violation_started_at is None:
            return False
        duration = (event.ts - event.violation_started_at).total_seconds()
        return duration > self.params["duration_min"] * 60

    def render_message(self, event: Event) -> str:
        return "You've drifted off your schedule — might want to fix that."
