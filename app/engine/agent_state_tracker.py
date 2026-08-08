from datetime import datetime


class AgentStateTracker:
    """Tracks each agent's current state and when they entered it. Lets
    duration-based rules answer "how long has this been true" without
    needing a new event to arrive."""

    def __init__(self) -> None:
        self._state: dict[str, tuple[str, datetime]] = {}  # agent_id -> (state, entered_at)

    def update(self, agent_id: str, new_state: str, at: datetime) -> None:
        self._state[agent_id] = (new_state, at)

    def all(self) -> dict[str, tuple[str, datetime]]:
        return dict(self._state)
