from httpx import ASGITransport, AsyncClient

from app.api.main import app


async def test_create_and_list_rule(clean_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/rules", json={
            "rule_type": "queue_backlog",
            "scope": {"queue_id": "billing"},
            "params": {"threshold": 20},
            "recipient_id": "lead_maria",
            "severity": 4,
            "description": "Notify me when billing backs up past 20",
        })
        assert response.status_code == 201
        created = response.json()
        assert created["rule_type"] == "queue_backlog"

        response = await client.get("/rules")
        assert response.status_code == 200
        rules = response.json()
        assert len(rules) == 1
        assert rules[0]["id"] == created["id"]


async def test_create_rule_with_unknown_type_is_rejected(clean_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/rules", json={
            "rule_type": "does_not_exist",
            "scope": {}, "params": {}, "recipient_id": "lead_maria",
            "severity": 1, "description": "...",
        })
        assert response.status_code == 422


async def test_update_rule_can_disable_it(clean_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = (await client.post("/rules", json={
            "rule_type": "queue_backlog", "scope": {"queue_id": "billing"},
            "params": {"threshold": 20}, "recipient_id": "lead_maria",
            "severity": 4, "description": "...",
        })).json()

        response = await client.patch(f"/rules/{created['id']}", json={"enabled": False})
        assert response.status_code == 200
        assert response.json()["enabled"] is False


async def test_list_notifications_starts_empty(clean_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/notifications")
        assert response.status_code == 200
        assert response.json() == []
