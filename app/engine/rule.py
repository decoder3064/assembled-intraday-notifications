from abc import ABC, abstractmethod

from app.ingestor.schemas import Event


class Rule(ABC):
    rule_type: str

    def __init__(self, rule_id: str, scope: dict, params: dict, recipient_id: str, severity: int):
        self.rule_id = rule_id
        self.scope = scope
        self.params = params
        self.recipient_id = recipient_id
        self.severity = severity

    @abstractmethod
    def entity_key(self, event: Event) -> str | None:
        """Which entity this event concerns, for this rule. None if the event doesn't apply here."""

    @abstractmethod
    def is_violating(self, event: Event) -> bool:
        """Whether the condition is currently true, given this event."""

    @abstractmethod
    def render_message(self, event: Event) -> str:
        ...

    def carry_over_state(self, previous: "Rule | None") -> None:
        """No-op by default — override if a rule keeps its own extra state."""
        pass


class DurationRule(Rule):
    """A rule that fires based on how long an agent has stayed in one state,
    checked on a timer rather than from an incoming event."""

    @abstractmethod
    def watched_state(self) -> str:
        """Which agent state this rule cares about, e.g. 'on_call'."""

    @abstractmethod
    def applies_to(self, agent_id: str) -> bool:
        """Is this agent within this rule's scope?"""

    @abstractmethod
    def is_too_long(self, seconds_in_state: float) -> bool:
        ...

    @abstractmethod
    def render_duration_message(self, agent_id: str, seconds_in_state: int) -> str:
        ...

    # a DurationRule never evaluates from an event directly
    def entity_key(self, event: Event) -> str | None:
        return None

    def is_violating(self, event: Event) -> bool:
        return False

    def render_message(self, event: Event) -> str:
        return ""
