from httpx import ASGITransport, AsyncClient

from app.api.main import app
from app.engine.engine import Engine
from app.engine.rules.queue_backlog import QueueBacklogRule
from app.ingestor.ingestor import Ingestor
from app.persistence.database import async_session
from app.persistence.models import RuleRow


def _snapshot(event_id, tickets_waiting):
    return {
        "event_id": event_id, "ts": "2026-05-26T09:15:00Z", "type": "queue_snapshot",
        "queue_id": "billing", "tickets_waiting": tickets_waiting, "longest_wait_sec": 90,
        "sla_target_sec": 120, "agents_available": 2, "agents_on_call": 3,
        "volume_last_15m": 15, "volume_forecast_next_15m": 20,
    }


async def _seed_engine(recipient="lead_maria", threshold=20):
    async with async_session() as session:
        row = RuleRow(
            rule_type="queue_backlog", scope={"queue_id": "billing"}, params={"threshold": threshold},
            recipient_id=recipient, description="...", severity=4,
        )
        session.add(row)
        await session.commit()
        rule_id = str(row.id)

    app.state.engine = Engine(rules=[
        QueueBacklogRule(rule_id=rule_id, scope={"queue_id": "billing"}, params={"threshold": threshold},
                          recipient_id=recipient, severity=4)
    ])
    app.state.ingestor = Ingestor()
    app.state.now = None


async def test_event_crossing_threshold_returns_and_persists_a_notification(clean_db):
    await _seed_engine()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/events", json=_snapshot("evt_1", tickets_waiting=25))
        assert response.status_code == 200
        assert len(response.json()["notifications"]) == 1

        notifications = (await client.get("/notifications")).json()
        assert len(notifications) == 1
        assert "25 tickets waiting" in notifications[0]["message"]


async def test_duplicate_event_produces_no_second_notification(clean_db):
    await _seed_engine()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/events", json=_snapshot("evt_1", tickets_waiting=25))
        response = await client.post("/events", json=_snapshot("evt_1", tickets_waiting=25))
        assert response.json()["notifications"] == []


async def test_malformed_event_returns_422(clean_db):
    await _seed_engine()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/events", json={"event_id": "evt_bad", "type": "queue_snapshot"})
        assert response.status_code == 422
