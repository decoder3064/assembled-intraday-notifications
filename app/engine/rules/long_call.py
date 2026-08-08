from app.engine.rule import DurationRule


class LongCallRule(DurationRule):
    rule_type = "long_call"
    default_severity = 6

    def watched_state(self) -> str:
        return "on_call"

    def applies_to(self, agent_id: str) -> bool:
        return agent_id in self.scope["agent_ids"]

    def is_too_long(self, seconds_in_state: float) -> bool:
        return seconds_in_state > self.params["duration_min"] * 60

    def render_duration_message(self, agent_id: str, seconds_in_state: int) -> str:
        minutes = seconds_in_state // 60
        return f"{agent_id} has been on a call for {minutes} min (threshold: {self.params['duration_min']})"
