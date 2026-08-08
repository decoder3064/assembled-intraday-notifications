from app.engine.engine import Engine
from app.engine.rules.long_call import LongCallRule
from app.engine.rules.queue_backlog import QueueBacklogRule
from app.replay import replay_file

DATA_PATH = "data/events.txt"


def _rules():
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


def test_replaying_the_real_sample_data_produces_the_expected_notifications():
    engine = Engine(rules=_rules())

    notifications = replay_file(DATA_PATH, engine)

    backlog_hits = [n for n in notifications if n.rule_id == "r_backlog"]
    long_call_hits = [n for n in notifications if n.rule_id == "r_long_call"]

    assert len(backlog_hits) == 1  # crosses 15 once at 9:30, recovers at 10:00, never re-crosses
    assert len(long_call_hits) == 2  # a_31 and a_11 each cross 45 min exactly once
