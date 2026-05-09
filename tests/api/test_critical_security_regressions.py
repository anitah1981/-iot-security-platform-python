"""Regression tests for high-impact auth and tenant-scoping bugs."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from routes import alerts as alerts_routes
from routes import devices as devices_routes


class _FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def skip(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def sort(self, *_args):
        return self

    async def to_list(self, length=None):
        if length is None:
            return list(self._docs)
        return list(self._docs)[:length]


class _RecordingDevices:
    def __init__(self, docs):
        self._docs = docs
        self.find_queries = []
        self.count_query = None

    def find(self, query):
        self.find_queries.append(query)
        return _FakeCursor(self._docs)

    async def count_documents(self, query):
        self.count_query = query
        return len(self._docs)


class _RecordingAlerts:
    def __init__(self, deleted_count=0):
        self.deleted_count = deleted_count
        self.delete_query = None

    async def delete_many(self, query):
        self.delete_query = query
        return SimpleNamespace(deleted_count=self.deleted_count)


class _FamilyMembers:
    async def find_one(self, *_args, **_kwargs):
        return None


def test_public_signup_rejects_admin_role(client: TestClient) -> None:
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Attacker",
            "email": "attacker@example.com",
            "password": "StrongPass123!",
            "role": "admin",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_device_name_search_preserves_user_scope(monkeypatch) -> None:
    user_id = ObjectId()
    db = SimpleNamespace(
        family_members=_FamilyMembers(),
        devices=_RecordingDevices([]),
    )
    monkeypatch.setattr(devices_routes, "get_database", AsyncMock(return_value=db))

    await devices_routes.get_devices(
        device_type=None,
        status=None,
        name="front.camera",
        page=1,
        limit=10,
        user={"_id": user_id},
    )

    query = db.devices.find_queries[0]
    assert "$and" in query
    visibility_filter, search_filter = query["$and"]
    assert visibility_filter["$or"] == [{"userId": user_id}, {"user_id": user_id}]
    assert visibility_filter["isDeleted"] == {"$ne": True}
    assert search_filter == {
        "$or": [
            {"name": {"$regex": "front\\.camera", "$options": "i"}},
            {"deviceId": {"$regex": "front\\.camera", "$options": "i"}},
        ]
    }


@pytest.mark.asyncio
async def test_alert_cleanup_is_scoped_to_current_user_devices(monkeypatch) -> None:
    user_id = ObjectId()
    device_id = ObjectId()
    db = SimpleNamespace(
        family_members=_FamilyMembers(),
        devices=_RecordingDevices([{"_id": device_id}]),
        alerts=_RecordingAlerts(deleted_count=2),
    )
    monkeypatch.setattr(alerts_routes, "get_database", AsyncMock(return_value=db))

    response = await alerts_routes.cleanup_old_alerts(days=30, user={"_id": user_id})

    assert response["deleted_count"] == 2
    query = db.alerts.delete_query
    assert query is not None
    device_clause, date_clause = query["$and"]
    assert device_clause == {
        "$or": [
            {"deviceId": {"$in": [device_id]}},
            {"device_id": {"$in": [device_id]}},
        ]
    }
    assert set(date_clause["$or"][0]["createdAt"].keys()) == {"$lt"}
    assert set(date_clause["$or"][1]["created_at"].keys()) == {"$lt"}
