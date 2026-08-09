from datetime import datetime


class AgentStateTracker:
    """Tracks each agent's current state and when they entered it. Lets
    duration-based rules answer "how long has this been true" without
    needing a new event to arrive."""

    def __init__(self) -> None:
        self._state: dict[str, tuple[str, datetime]] = {}  # agent_id -> (state, entered_at)

    def update(self, agent_id: str, new_state: str, at: datetime) -> None:
        current = self._state.get(agent_id)
        if current is not None and at < current[1]:
            return  # a late-arriving event, older than what we already have — ignore it
        self._state[agent_id] = (new_state, at)

    def all(self) -> dict[str, tuple[str, datetime]]:
        return dict(self._state)
