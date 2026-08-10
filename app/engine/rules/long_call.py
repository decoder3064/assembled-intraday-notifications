from app.util.agent_names import format_agent_name
from app.util.duration import format_duration
from app.engine.rule import DurationRule


class LongCallRule(DurationRule):
    rule_type = "long_call"

    def watched_state(self) -> str:
        return "on_call"

    def applies_to(self, agent_id: str) -> bool:
        return agent_id.strip() in {a.strip() for a in self.scope["agent_ids"]}

    def is_too_long(self, seconds_in_state: float) -> bool:
        return seconds_in_state > self.params["duration_min"] * 60

    def render_duration_message(self, agent_id: str, seconds_in_state: int) -> str:
        threshold_sec = self.params["duration_min"] * 60
        overage = format_duration(seconds_in_state - threshold_sec)
        return (
            f"{format_agent_name(agent_id)} has been on one call for {format_duration(seconds_in_state)} now, "
            f"{overage} past your {format_duration(threshold_sec)} limit"
        )
