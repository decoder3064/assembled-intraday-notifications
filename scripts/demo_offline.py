import argparse
import json
import time
from datetime import datetime

from app.engine.engine import Engine
from app.engine.rules.long_call import LongCallRule
from app.engine.rules.queue_backlog import QueueBacklogRule
from app.ingestor.ingestor import Ingestor
from app.router.router import console_delivery

DATA_PATH = "data/events.txt"


def _default_rules():
    return [
        QueueBacklogRule(
            rule_id="r_backlog", scope={"queue_id": "billing"}, params={"threshold": 15},
            recipient_id="lead_maria", severity=4,
        ),
        LongCallRule(
            rule_id="r_long_call", scope={"agent_ids": ["a_31", "a_11"]}, params={"duration_min": 45},
            recipient_id="lead_maria", severity=6,
        ),
    ]


def _summarize(event) -> str:
    ts = event.ts.strftime("%H:%M:%S")
    if event.type == "queue_snapshot":
        return f"[{ts}] queue_snapshot      {event.queue_id}: {event.tickets_waiting} waiting, longest wait {event.longest_wait_sec}s"
    if event.type == "agent_state_change":
        return f"[{ts}] agent_state_change  {event.agent_id}: {event.previous_state} -> {event.new_state}"
    return f"[{ts}] adherence_check     {event.agent_id}: in_violation={event.in_violation}"


def run(speed: float) -> None:
    ingestor = Ingestor()
    engine = Engine(rules=_default_rules())

    previous_ts: datetime | None = None
    now: datetime | None = None

    with open(DATA_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            event = ingestor.process(json.loads(line))
            if event is None:
                continue  # duplicate, dropped silently same as production

            if previous_ts is not None:
                gap = max(0.0, (event.ts - previous_ts).total_seconds())
                time.sleep(gap / speed)
            previous_ts = event.ts

            print(_summarize(event))

            notifications = engine.on_event(event)
            now = event.ts if now is None else max(now, event.ts)
            notifications += engine.tick(now)

            for n in notifications:
                print(">>> NOTIFICATION", end=" ")
                console_delivery(n)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay the sample event feed as a live demo.")
    parser.add_argument("--speed", type=float, default=18.0, help="speed-up factor; 18 compresses the ~90 real minutes into ~5 demo minutes")
    args = parser.parse_args()
    run(args.speed)
