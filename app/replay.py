import json
from datetime import datetime

from app.engine.engine import Engine, Notification
from app.ingestor.ingestor import Ingestor


def replay_file(path: str, engine: Engine) -> list[Notification]:
    """Feed a JSONL event file through the ingestor and engine, in file
    order. Tracks the latest event time seen so far, so a late or
    duplicate event can't move time backward for tick-based rules."""
    ingestor = Ingestor()
    notifications: list[Notification] = []
    now: datetime | None = None

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = ingestor.process(json.loads(line))
            if event is None:
                continue

            notifications.extend(engine.on_event(event))
            now = event.ts if now is None else max(now, event.ts)
            notifications.extend(engine.tick(now))

    return notifications
