import pytest
from pydantic import ValidationError

from app.ingestor.ingestor import Ingestor, UnknownEventType


def test_valid_queue_snapshot_parses():
    ingestor = Ingestor()
    event = ingestor.process({
        "event_id": "evt_1", "ts": "2026-05-26T09:00:00Z", "type": "queue_snapshot",
        "queue_id": "billing", "tickets_waiting": 0, "longest_wait_sec": 0,
        "sla_target_sec": 120, "agents_available": 0, "agents_on_call": 0,
        "volume_last_15m": 6, "volume_forecast_next_15m": 22,
    })
    assert event.queue_id == "billing"


def test_duplicate_event_id_is_dropped():
    ingestor = Ingestor()
    raw = {
        "event_id": "evt_01HXYZ050", "ts": "2026-05-26T09:36:00Z", "type": "adherence_check",
        "agent_id": "a_19", "queue_ids": ["billing"], "scheduled_state": "available",
        "actual_state": "on_break", "in_violation": True,
        "violation_started_at": "2026-05-26T09:35:00Z",
    }
    assert ingestor.process(raw) is not None
    raw_repeat = {**raw, "ts": "2026-05-26T09:36:30Z"}  # the real repeat had a different ts
    assert ingestor.process(raw_repeat) is None


def test_null_queue_ids_normalizes_to_empty_list():
    ingestor = Ingestor()
    event = ingestor.process({
        "event_id": "evt_2", "ts": "2026-05-26T10:01:40Z", "type": "agent_state_change",
        "agent_id": "a_05", "queue_ids": None, "previous_state": "available",
        "previous_state_duration_sec": 3610, "new_state": "on_call",
    })
    assert event.queue_ids == []


def test_missing_forecast_stays_none_not_zero():
    ingestor = Ingestor()
    event = ingestor.process({
        "event_id": "evt_3", "ts": "2026-05-26T10:00:00Z", "type": "queue_snapshot",
        "queue_id": "billing", "tickets_waiting": 14, "longest_wait_sec": 200,
        "sla_target_sec": 120, "agents_available": 1, "agents_on_call": 3,
        "volume_last_15m": 30, "volume_forecast_next_15m": None,
    })
    assert event.volume_forecast_next_15m is None


def test_unknown_event_type_raises():
    ingestor = Ingestor()
    with pytest.raises(UnknownEventType):
        ingestor.process({"event_id": "evt_4", "ts": "2026-05-26T10:00:00Z", "type": "something_new"})


def test_malformed_event_raises_validation_error():
    ingestor = Ingestor()
    with pytest.raises(ValidationError):
        ingestor.process({"event_id": "evt_5", "type": "queue_snapshot"})  # missing required fields
