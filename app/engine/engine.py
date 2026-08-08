from datetime import datetime

from app.engine.agent_state_tracker import AgentStateTracker
from app.engine.rule import DurationRule, Rule
from app.engine.rule_state import RuleStateTracker
from app.ingestor.schemas import Event


class Notification:
    def __init__(self, rule: Rule, message: str):
        self.rule_id = rule.rule_id
        self.recipient_id = rule.recipient_id
        self.severity = rule.severity
        self.message = message


class Engine:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules
        self.state = RuleStateTracker()
        self.agent_states = AgentStateTracker()

    def set_rules(self, rules: list[Rule]) -> None:
        self.rules = rules

    def on_event(self, event: Event) -> list[Notification]:
        if event.type == "agent_state_change":
            self.agent_states.update(event.agent_id, event.new_state, event.ts)

        notifications = []
        for rule in self.rules:
            entity_key = rule.entity_key(event)
            if entity_key is None:
                continue
            violating = rule.is_violating(event)
            if self.state.update(rule.rule_id, entity_key, violating):
                notifications.append(Notification(rule, rule.render_message(event)))
        return notifications

    def tick(self, now: datetime) -> list[Notification]:
        notifications = []
        for rule in self.rules:
            if not isinstance(rule, DurationRule):
                continue
            for agent_id, (state, entered_at) in self.agent_states.all().items():
                if state != rule.watched_state() or not rule.applies_to(agent_id):
                    continue
                seconds = (now - entered_at).total_seconds()
                violating = rule.is_too_long(seconds)
                if self.state.update(rule.rule_id, agent_id, violating):
                    notifications.append(
                        Notification(rule, rule.render_duration_message(agent_id, int(seconds)))
                    )
        return notifications
