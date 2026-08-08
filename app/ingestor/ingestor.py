from app.ingestor.schemas import AdherenceCheck, AgentStateChange, Event, QueueSnapshot

_EVENT_MODELS: dict[str, type] = {
    "queue_snapshot": QueueSnapshot,
    "agent_state_change": AgentStateChange,
    "adherence_check": AdherenceCheck,
}


class UnknownEventType(ValueError):
    pass


class Ingestor:
    def __init__(self) -> None:
        self._seen_event_ids: set[str] = set()

    def process(self, raw: dict) -> Event | None:
        """Validate and normalize a raw event; return None if it's a duplicate."""
        model = _EVENT_MODELS.get(raw.get("type"))
        if model is None:
            raise UnknownEventType(f"unrecognized event type: {raw.get('type')!r}")

        event = model.model_validate(raw)

        if event.event_id in self._seen_event_ids:
            return None

        self._seen_event_ids.add(event.event_id)
        return event
