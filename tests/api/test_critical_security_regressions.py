from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.background import BackgroundTasks

from models import AlertCreate


class _Cursor:
    def __init__(self, rows):
        self.rows = rows

    def skip(self, _n):
        return self

    def limit(self, _n):
        return self

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, length=None):
        return self.rows if length is None else self.rows[:length]


class _Collection:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.find_filters = []
        self.delete_filters = []
        self.inserted = []
        self.find_one = AsyncMock(return_value=None)
        self.update_one = AsyncMock(return_value=SimpleNamespace(matched_count=1, modified_count=1))
        self.update_many = AsyncMock(return_value=SimpleNamespace(modified_count=0))

    def find(self, query=None):
        self.find_filters.append(query or {})
        return _Cursor(self.rows)

    async def count_documents(self, query):
        return len(self.rows)

    async def delete_many(self, query):
        self.delete_filters.append(query)
        return SimpleNamespace(deleted_count=1)

    async def insert_one(self, doc):
        self.inserted.append(doc)
        return SimpleNamespace(inserted_id=ObjectId())


def test_public_signup_cannot_request_admin_role(client: TestClient):
    r = client.post(
        "/api/auth/signup",
        json={
            "name": "Mallory",
            "email": "mallory@example.com",
            "password": "Str0ng!Password123",
            "role": "admin",
        },
    )

    assert r.status_code == 422


def test_alert_create_requires_auth(client: TestClient):
    r = client.post(
        "/api/alerts",
        json={
            "device_id": str(ObjectId()),
            "message": "Forged alert",
            "severity": "critical",
            "type": "security",
        },
    )

    assert r.status_code in (401, 403)


def test_alert_cleanup_requires_auth(client: TestClient):
    r = client.delete("/api/alerts/cleanup?days=30")

    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_device_name_search_preserves_owner_scope(monkeypatch):
    from routes import devices

    user_id = ObjectId()
    db = SimpleNamespace(
        family_members=SimpleNamespace(find_one=AsyncMock(return_value=None)),
        devices=_Collection(rows=[]),
    )
    monkeypatch.setattr(devices, "get_database", AsyncMock(return_value=db))

    await devices.get_devices(name="Camera.*", user={"_id": user_id})

    query = db.devices.find_filters[0]
    assert query["isDeleted"] == {"$ne": True}
    assert "$and" in query
    assert {"$or": [{"userId": user_id}, {"user_id": user_id}]} in query["$and"]
    assert {
        "$or": [
            {"name": {"$regex": "Camera\\.\\*", "$options": "i"}},
            {"deviceId": {"$regex": "Camera\\.\\*", "$options": "i"}},
        ]
    } in query["$and"]


@pytest.mark.asyncio
async def test_alert_cleanup_only_deletes_current_users_alerts(monkeypatch):
    from routes import alerts

    user_id = ObjectId()
    device_id = ObjectId()
    db = SimpleNamespace(
        family_members=SimpleNamespace(find_one=AsyncMock(return_value=None)),
        devices=_Collection(rows=[{"_id": device_id, "userId": user_id, "isDeleted": False}]),
        alerts=_Collection(rows=[]),
    )
    monkeypatch.setattr(alerts, "get_database", AsyncMock(return_value=db))

    result = await alerts.cleanup_old_alerts(days=30, user={"_id": user_id})

    assert result["deleted_count"] == 1
    delete_query = db.alerts.delete_filters[0]
    assert {"deviceId": {"$in": [device_id]}} in delete_query["$and"][0]["$or"]
    assert {"device_id": {"$in": [device_id]}} in delete_query["$and"][0]["$or"]


@pytest.mark.asyncio
async def test_authenticated_alert_create_rejects_unowned_device(monkeypatch):
    from routes import alerts

    user_id = ObjectId()
    owned_device_id = ObjectId()
    other_device_id = ObjectId()
    db = SimpleNamespace(
        family_members=SimpleNamespace(find_one=AsyncMock(return_value=None)),
        devices=_Collection(rows=[{"_id": owned_device_id, "userId": user_id, "isDeleted": False}]),
        alerts=_Collection(rows=[]),
    )
    monkeypatch.setattr(alerts, "get_database", AsyncMock(return_value=db))

    with pytest.raises(HTTPException) as exc:
        await alerts.create_alert(
            AlertCreate(
                device_id=str(other_device_id),
                message="Forged alert",
                severity="critical",
                type="security",
            ),
            BackgroundTasks(),
            user={"_id": user_id},
        )

    assert exc.value.status_code == 403
    assert db.alerts.inserted == []


@pytest.mark.asyncio
async def test_websocket_rejects_cross_user_room_join(monkeypatch):
    from services import websocket_service

    emitted = []
    entered = []
    monkeypatch.setattr(websocket_service.sio, "emit", AsyncMock(side_effect=lambda *a, **k: emitted.append((a, k))))
    monkeypatch.setattr(websocket_service.sio, "enter_room", lambda sid, room: entered.append((sid, room)))
    websocket_service.connected_users["sid-1"] = {
        "user_id": "user-a",
        "connected_at": datetime.utcnow().isoformat(),
        "rooms": ["user_user-a"],
    }

    try:
        await websocket_service.join_room("sid-1", {"room": "user_user-b"})
    finally:
        websocket_service.connected_users.pop("sid-1", None)

    assert entered == []
    assert emitted
    assert emitted[0][0][0] == "room_error"
