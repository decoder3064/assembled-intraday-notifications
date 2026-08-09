from app.engine.rule import Rule
from app.ingestor.schemas import Event


class VolumeSurgeRule(Rule):
    rule_type = "volume_surge"

    def entity_key(self, event: Event) -> str | None:
        if event.type != "queue_snapshot" or event.queue_id.strip() != self.scope["queue_id"].strip():
            return None
    
        if event.volume_forecast_next_15m is None:
            return None
        return event.queue_id

    def is_violating(self, event: Event) -> bool:
        forecast = event.volume_forecast_next_15m
        return event.volume_last_15m > forecast * (1 + self.params["pct_over_forecast"])

    def render_message(self, event: Event) -> str:
        return f"{event.queue_id} got {event.volume_last_15m} calls in the last 15 minutes, more than the {event.volume_forecast_next_15m} you expected"
