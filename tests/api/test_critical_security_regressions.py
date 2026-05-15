from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pydantic import ValidationError

from models import UserCreate


def test_public_signup_schema_rejects_admin_role() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            name="Mallory",
            email="mallory@example.com",
            password="StrongPass123!",
            role="admin",
        )


class _FakeCursor:
    def __init__(self, docs=None):
        self.docs = docs or []

    def skip(self, _value):
        return self

    def limit(self, _value):
        return self

    def sort(self, _value):
        return self

    async def to_list(self, length=None):
        return self.docs[:length] if length else list(self.docs)


@pytest.mark.asyncio
async def test_device_name_search_preserves_owner_scope(monkeypatch) -> None:
    import routes.devices as devices

    user_id = ObjectId()
    queries = []

    class _DevicesCollection:
        def find(self, query):
            queries.append(query)
            return _FakeCursor([])

        async def count_documents(self, query):
            queries.append(query)
            return 0

    db = MagicMock()
    db.devices = _DevicesCollection()

    monkeypatch.setattr(devices, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr(devices, "_get_user_family_id", AsyncMock(return_value=None))

    await devices.get_devices(
        name="Camera.*",
        page=1,
        limit=10,
        user={"_id": user_id},
    )

    assert queries, "devices.find should be called"
    query = queries[0]
    assert "$and" in query
    assert {"$or": [{"userId": user_id}, {"user_id": user_id}]} in query["$and"]
    assert {"isDeleted": {"$ne": True}} in query["$and"]

    search_clause = next(
        clause for clause in query["$and"]
        if "$or" in clause and {"userId": user_id} not in clause["$or"]
    )
    assert search_clause == {
        "$or": [
            {"name": {"$regex": "Camera\\.\\*", "$options": "i"}},
            {"deviceId": {"$regex": "Camera\\.\\*", "$options": "i"}},
        ]
    }


def test_alert_cleanup_requires_authentication(client: TestClient, mock_db) -> None:
    alerts = MagicMock()
    alerts.delete_many = AsyncMock(return_value=MagicMock(deleted_count=10))
    mock_db.alerts = alerts

    response = client.delete("/api/alerts/cleanup?days=30")

    assert response.status_code in (401, 403)
    alerts.delete_many.assert_not_called()


@pytest.mark.asyncio
async def test_alert_cleanup_scopes_delete_to_current_user_devices(monkeypatch) -> None:
    import routes.alerts as alerts_route

    user_id = ObjectId()
    device_id = ObjectId()
    captured = {}

    class _AlertsCollection:
        async def delete_many(self, query):
            captured["query"] = query
            return MagicMock(deleted_count=1)

    db = MagicMock()
    db.alerts = _AlertsCollection()

    monkeypatch.setattr(alerts_route, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr(
        alerts_route,
        "_device_ids_for_user_alerts",
        AsyncMock(return_value=[device_id]),
    )

    result = await alerts_route.cleanup_old_alerts(days=30, user={"_id": user_id})

    assert result["deleted_count"] == 1
    query = captured["query"]
    assert "$and" in query
    assert {
        "$or": [
            {"deviceId": {"$in": [device_id]}},
            {"device_id": {"$in": [device_id]}},
        ]
    } in query["$and"]
