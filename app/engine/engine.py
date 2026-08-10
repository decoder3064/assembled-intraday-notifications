import logging
from datetime import datetime

from app.engine.agent_state_tracker import AgentStateTracker
from app.engine.rule import DurationRule, Rule
from app.engine.rule_state import RuleStateTracker
from app.ingestor.schemas import Event

logger = logging.getLogger(__name__)


class Notification:
    def __init__(self, rule: Rule, message: str):
        self.rule_id = rule.rule_id
        self.rule_type = rule.rule_type
        self.recipient_id = rule.recipient_id
        self.severity = rule.severity
        self.message = message


class Engine:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules
        self.state = RuleStateTracker()
        self.agent_states = AgentStateTracker()

    def set_rules(self, rules: list[Rule]) -> None:
        old_by_id = {r.rule_id: r for r in self.rules}
        for new_rule in rules:
            new_rule.carry_over_state(old_by_id.get(new_rule.rule_id))
        self.rules = rules

    def on_event(self, event: Event) -> list[Notification]:
        if event.type == "agent_state_change":
            self.agent_states.update(event.agent_id, event.new_state, event.ts)

        notifications = []
        for rule in self.rules:
            try:
                entity_key = rule.entity_key(event)
                if entity_key is None:
                    continue
                violating = rule.is_violating(event)
                if self.state.update(rule.rule_id, entity_key, violating, event.ts):
                    notifications.append(Notification(rule, rule.render_message(event)))
            except Exception:
                # A misconfigured rule (e.g. a missing required param) shouldn't
                # stop every other rule from evaluating against this event.
                logger.exception("rule %s failed to evaluate event %s", rule.rule_id, event.event_id)
        return notifications

    def tick(self, now: datetime) -> list[Notification]:
        notifications = []
        for rule in self.rules:
            if not isinstance(rule, DurationRule):
                continue
            for agent_id, (state, entered_at) in self.agent_states.all().items():
                try:
                    if not rule.applies_to(agent_id):
                        continue
                    seconds = 0
                    violating = False
                    if state == rule.watched_state():
                        seconds = (now - entered_at).total_seconds()
                        violating = rule.is_too_long(seconds)
                    if self.state.update(rule.rule_id, agent_id, violating, now):
                        notifications.append(
                            Notification(rule, rule.render_duration_message(agent_id, int(seconds)))
                        )
                except Exception:
                    logger.exception("rule %s failed to evaluate agent %s", rule.rule_id, agent_id)
        return notifications
