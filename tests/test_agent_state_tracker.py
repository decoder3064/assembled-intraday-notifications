from datetime import datetime, timezone

from app.engine.agent_state_tracker import AgentStateTracker


def test_late_arriving_event_does_not_overwrite_newer_state():
    tracker = AgentStateTracker()
    tracker.update("a_19", "on_call", datetime(2026, 5, 26, 9, 30, tzinfo=timezone.utc))

    # An older, late-arriving event must not overwrite the newer state.
    tracker.update("a_19", "available", datetime(2026, 5, 26, 9, 10, tzinfo=timezone.utc))

    state, entered_at = tracker.all()["a_19"]
    assert state == "on_call"
    assert entered_at == datetime(2026, 5, 26, 9, 30, tzinfo=timezone.utc)


def test_newer_event_still_updates_state_normally():
    tracker = AgentStateTracker()
    tracker.update("a_19", "on_call", datetime(2026, 5, 26, 9, 30, tzinfo=timezone.utc))
    tracker.update("a_19", "available", datetime(2026, 5, 26, 9, 45, tzinfo=timezone.utc))

    state, entered_at = tracker.all()["a_19"]
    assert state == "available"
    assert entered_at == datetime(2026, 5, 26, 9, 45, tzinfo=timezone.utc)
