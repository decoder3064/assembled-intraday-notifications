from dataclasses import dataclass


@dataclass
class RuleState:
    status: str = "ok"  # "ok" | "firing"


class RuleStateTracker:
    """Tracks whether each (rule, entity) pair is currently firing, so a rule
    only produces a notification on the ok -> firing transition, not on every
    event while the condition stays true."""

    def __init__(self) -> None:
        self._state: dict[tuple[str, str], RuleState] = {}

    def update(self, rule_id: str, entity_key: str, is_violating: bool) -> bool:
        """Returns True if this is a fresh transition into 'firing'."""
        key = (rule_id, entity_key)
        state = self._state.setdefault(key, RuleState())

        just_started_firing = is_violating and state.status == "ok"
        state.status = "firing" if is_violating else "ok"
        return just_started_firing
