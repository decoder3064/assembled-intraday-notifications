from app.engine.rule import Rule
from app.ingestor.schemas import Event


class TeamAdherenceCapacityRule(Rule):
    """Aggregates violation state across agents itself, since no single
    adherence_check event knows about anyone but itself. carry_over_state()
    preserves that tally (and last-seen timestamps, for the late-event
    guard) across a rule-cache refresh."""

    rule_type = "team_adherence_capacity"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._violating_agents: set[str] = set()
        self._last_seen: dict[str, object] = {}

    def carry_over_state(self, previous: Rule | None) -> None:
        if isinstance(previous, TeamAdherenceCapacityRule):
            self._violating_agents = previous._violating_agents
            self._last_seen = previous._last_seen

    def entity_key(self, event: Event) -> str | None:
        if event.type != "adherence_check" or event.agent_id.strip() not in {
            a.strip() for a in self.scope["agent_ids"]
        }:
            return None

        last = self._last_seen.get(event.agent_id)
        if last is not None and event.ts < last:
            return "team"  # late-arriving event, older than what we already have — ignore it

        self._last_seen[event.agent_id] = event.ts
        if event.in_violation:
            self._violating_agents.add(event.agent_id)
        else:
            self._violating_agents.discard(event.agent_id)

        return "team"

    def is_violating(self, event: Event) -> bool:
        return len(self._violating_agents) > self.params["count_threshold"]

    def render_message(self, event: Event) -> str:
        return f"{len(self._violating_agents)} of your agents are off schedule right now"
