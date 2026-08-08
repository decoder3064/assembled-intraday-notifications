from app.engine.rule import Rule
from app.ingestor.schemas import Event


class TeamAdherenceCapacityRule(Rule):
    """Structurally different from the other rules here: it aggregates
    across every agent in scope instead of reading one event in isolation.
    Tracks which agents are currently in violation internally, since no
    single adherence_check event knows about anyone but itself.

    That internal tracking would normally be wiped every time the
    rule-cache poller rebuilds this rule from the database (~every 5s) —
    carry_over_state() below is what prevents that, by copying the tally
    from the previous instance into the new one during a refresh."""

    rule_type = "team_adherence_capacity"
    default_severity = 8

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._violating_agents: set[str] = set()

    def carry_over_state(self, previous: Rule | None) -> None:
        if isinstance(previous, TeamAdherenceCapacityRule):
            self._violating_agents = previous._violating_agents

    def entity_key(self, event: Event) -> str | None:
        if event.type != "adherence_check" or event.agent_id.strip() not in {
            a.strip() for a in self.scope["agent_ids"]
        }:
            return None

        if event.in_violation:
            self._violating_agents.add(event.agent_id)
        else:
            self._violating_agents.discard(event.agent_id)

        return "team"

    def is_violating(self, event: Event) -> bool:
        return len(self._violating_agents) > self.params["count_threshold"]

    def render_message(self, event: Event) -> str:
        return (
            f"{len(self._violating_agents)} of your agents are currently out of adherence "
            f"(threshold: {self.params['count_threshold']})"
        )
