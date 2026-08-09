import argparse
import json
import time
from datetime import datetime

import httpx

DATA_PATH = "data/events.txt"


def _summarize(raw: dict) -> str:
    ts, t = raw["ts"], raw["type"]
    if t == "queue_snapshot":
        return f"[{ts}] queue_snapshot      {raw['queue_id']}: {raw['tickets_waiting']} waiting, longest wait {raw['longest_wait_sec']}s"
    if t == "agent_state_change":
        return f"[{ts}] agent_state_change  {raw['agent_id']}: {raw['previous_state']} -> {raw['new_state']}"
    return f"[{ts}] adherence_check     {raw['agent_id']}: in_violation={raw['in_violation']}"


def run(speed: float, base_url: str) -> None:
    previous_ts: datetime | None = None

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        with open(DATA_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)

                ts = datetime.fromisoformat(raw["ts"])
                if previous_ts is not None:
                    time.sleep(max(0.0, (ts - previous_ts).total_seconds()) / speed)
                previous_ts = ts

                print(_summarize(raw))

                response = client.post("/events", json=raw)
                response.raise_for_status()
                for message in response.json()["notifications"]:
                    print(">>> NOTIFICATION", message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay the sample event feed against a running server, using its real rules and database.")
    parser.add_argument("--speed", type=float, default=30.0, help="speed-up factor; 30 compresses the ~90 real minutes into ~3 demo minutes")
    parser.add_argument("--base-url", default="http://127.0.0.1:8020")
    args = parser.parse_args()
    run(args.speed, args.base_url)
