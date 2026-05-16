from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from models import UserCreate


class _Cursor:
    def __init__(self, docs=None):
        self.docs = docs or []

    def skip(self, _):
        return self

    def limit(self, _):
        return self

    def sort(self, *_):
        return self

    async def to_list(self, length=None):
        return self.docs[:length] if length else self.docs


class _Collection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.find_queries = []
        self.deleted_query = None

    async def find_one(self, _):
        return None

    def find(self, query=None):
        self.find_queries.append(query or {})
        return _Cursor(self.docs)

    async def count_documents(self, _):
        return len(self.docs)

    async def delete_many(self, query):
        self.deleted_query = query
        return type("DeleteResult", (), {"deleted_count": 0})()


def test_public_signup_schema_rejects_admin_role():
    with pytest.raises(Exception):
        UserCreate(
            name="Eve",
            email="eve@example.com",
            password="AAaa11!!bbbb",
            role="admin",
        )


def test_alert_cleanup_requires_authentication(client: TestClient):
    response = client.delete("/api/alerts/cleanup?days=30")
    assert response.status_code in (401, 403)


def test_alert_create_requires_authentication(client: TestClient):
    response = client.post(
        "/api/alerts",
        json={
            "device_id": str(ObjectId()),
            "message": "Injected alert",
            "severity": "critical",
            "type": "security",
        },
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_device_name_search_preserves_user_scope(monkeypatch):
    from routes import devices as devices_routes

    user_id = ObjectId()
    devices = _Collection([])
    fake_db = type(
        "FakeDb",
        (),
        {
            "devices": devices,
            "family_members": _Collection([]),
        },
    )()

    async def fake_get_database():
        return fake_db

    monkeypatch.setattr(devices_routes, "get_database", fake_get_database)

    await devices_routes.get_devices(name="cam.*", page=1, limit=10, user={"_id": user_id})

    query = devices.find_queries[-1]
    assert "$or" not in query
    assert {"$or": [{"userId": user_id}, {"user_id": user_id}]} in query["$and"]
    assert {
        "$or": [
            {"name": {"$regex": "cam\\.\\*", "$options": "i"}},
            {"deviceId": {"$regex": "cam\\.\\*", "$options": "i"}},
        ]
    } in query["$and"]


@pytest.mark.asyncio
async def test_alert_cleanup_scopes_delete_to_current_users_devices(monkeypatch):
    from routes import alerts as alerts_routes

    user_id = ObjectId()
    device_id = ObjectId()
    alerts = _Collection([])
    fake_db = type(
        "FakeDb",
        (),
        {
            "devices": _Collection([{"_id": device_id, "userId": user_id}]),
            "alerts": alerts,
            "family_members": _Collection([]),
        },
    )()

    async def fake_get_database():
        return fake_db

    monkeypatch.setattr(alerts_routes, "get_database", fake_get_database)

    await alerts_routes.cleanup_old_alerts(days=30, user={"_id": user_id})

    delete_query = alerts.deleted_query
    assert delete_query is not None
    assert {
        "$or": [
            {"deviceId": {"$in": [device_id]}},
            {"device_id": {"$in": [device_id]}},
        ]
    } in delete_query["$and"]
    assert any("createdAt" in branch or "created_at" in branch for branch in delete_query["$and"][1]["$or"])


@pytest.mark.asyncio
async def test_websocket_join_room_rejects_other_user_room(monkeypatch):
    from services import websocket_service

    entered_rooms = []
    websocket_service.connected_users.clear()
    websocket_service.connected_users["sid-1"] = {
        "user_id": "user-a",
        "connected_at": "now",
        "rooms": ["user_user-a"],
    }

    def fake_enter_room(sid, room):
        entered_rooms.append((sid, room))

    emit = AsyncMock()
    monkeypatch.setattr(websocket_service.sio, "enter_room", fake_enter_room)
    monkeypatch.setattr(websocket_service.sio, "emit", emit)

    await websocket_service.join_room("sid-1", {"room": "user_user-b"})

    assert entered_rooms == []
    emit.assert_awaited_with(
        "room_error",
        {"room": "user_user-b", "error": "not allowed"},
        to="sid-1",
    )

    await websocket_service.join_room("sid-1", {"room": "user_user-a"})

    assert entered_rooms == [("sid-1", "user_user-a")]
