from app.engine.rule import Rule
from app.ingestor.schemas import Event


class TeamAdherenceCapacityRule(Rule):
    """Unlike the other rules, this one keeps its own state across events —
    no single adherence_check knows about more than one agent."""

    rule_type = "team_adherence_capacity"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._violating_agents: set[str] = set()
        self._last_seen: dict[str, object] = {}

    def carry_over_state(self, previous: Rule | None) -> None:
        if isinstance(previous, TeamAdherenceCapacityRule):
            scoped_ids = {a.strip() for a in self.scope["agent_ids"]}
            self._violating_agents = previous._violating_agents & scoped_ids
            self._last_seen = {k: v for k, v in previous._last_seen.items() if k in scoped_ids}

    def entity_key(self, event: Event) -> str | None:
        agent_id = event.agent_id.strip()
        if event.type != "adherence_check" or agent_id not in {
            a.strip() for a in self.scope["agent_ids"]
        }:
            return None

        last = self._last_seen.get(agent_id)
        if last is not None and event.ts < last:
            return "team"  # late-arriving event, older than what we already have — ignore it

        self._last_seen[agent_id] = event.ts
        if event.in_violation:
            self._violating_agents.add(agent_id)
        else:
            self._violating_agents.discard(agent_id)

        return "team"

    def is_violating(self, event: Event) -> bool:
        return len(self._violating_agents) > self.params["count_threshold"]

    def render_message(self, event: Event) -> str:
        return f"{len(self._violating_agents)} of your agents are off schedule right now"
