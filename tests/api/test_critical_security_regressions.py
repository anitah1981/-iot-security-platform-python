from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import re

import pytest
from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException
from pydantic import ValidationError

from models import AlertCreate, UserCreate
import routes.agent_security as agent_security_routes
import routes.alerts as alert_routes
import routes.devices as device_routes
import services.websocket_service as websocket_service


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def skip(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, length=None):
        if length is None:
            return list(self.docs)
        return list(self.docs)[:length]


def test_public_signup_rejects_admin_role():
    with pytest.raises(ValidationError):
        UserCreate(
            name="Attacker",
            email="attacker@example.com",
            password="StrongPass123!",
            role="admin",
        )


@pytest.mark.asyncio
async def test_device_name_search_preserves_user_scope(monkeypatch):
    user_id = ObjectId()
    db = MagicMock()
    db.family_members.find_one = AsyncMock(return_value=None)
    db.devices.find = MagicMock(return_value=FakeCursor([]))
    db.devices.count_documents = AsyncMock(return_value=0)
    monkeypatch.setattr(device_routes, "get_database", AsyncMock(return_value=db))

    await device_routes.get_devices(name="Victim.*", user={"_id": user_id})

    query = db.devices.find.call_args.args[0]
    assert query["isDeleted"] == {"$ne": True}
    assert "$and" in query
    owner_clause, search_clause = query["$and"]
    assert {"userId": user_id} in owner_clause["$or"]
    assert {"user_id": user_id} in owner_clause["$or"]
    assert search_clause["$or"][0]["name"]["$regex"] == re.escape("Victim.*")
    assert search_clause["$or"][1]["deviceId"]["$regex"] == re.escape("Victim.*")


@pytest.mark.asyncio
async def test_alert_create_rejects_cross_tenant_device(monkeypatch):
    user_id = ObjectId()
    owned_device_id = ObjectId()
    other_device_id = ObjectId()
    db = MagicMock()
    db.family_members.find_one = AsyncMock(return_value=None)
    db.devices.find = MagicMock(return_value=FakeCursor([{"_id": owned_device_id}]))
    db.alerts.insert_one = AsyncMock()
    monkeypatch.setattr(alert_routes, "get_database", AsyncMock(return_value=db))

    alert = AlertCreate(
        device_id=str(other_device_id),
        message="Cross-tenant test",
        severity="critical",
        type="security",
    )

    with pytest.raises(HTTPException) as exc:
        await alert_routes.create_alert(alert, BackgroundTasks(), user={"_id": user_id})

    assert exc.value.status_code == 403
    db.alerts.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_alert_cleanup_is_scoped_to_current_user_devices(monkeypatch):
    user_id = ObjectId()
    owned_device_id = ObjectId()
    db = MagicMock()
    db.family_members.find_one = AsyncMock(return_value=None)
    db.devices.find = MagicMock(return_value=FakeCursor([{"_id": owned_device_id}]))
    db.alerts.delete_many = AsyncMock(return_value=SimpleNamespace(deleted_count=2))
    monkeypatch.setattr(alert_routes, "get_database", AsyncMock(return_value=db))

    response = await alert_routes.cleanup_old_alerts(days=30, user={"_id": user_id})

    assert response["deleted_count"] == 2
    query = db.alerts.delete_many.call_args.args[0]
    device_clause, date_clause = query["$and"]
    assert {"deviceId": {"$in": [owned_device_id]}} in device_clause["$or"]
    assert {"device_id": {"$in": [owned_device_id]}} in device_clause["$or"]
    assert "createdAt" in date_clause["$or"][0]


@pytest.mark.asyncio
async def test_websocket_rejects_joining_another_users_room(monkeypatch):
    owner_id = str(ObjectId())
    other_id = str(ObjectId())
    websocket_service.connected_users.clear()
    websocket_service.connected_users["sid-1"] = {
        "user_id": owner_id,
        "rooms": [f"user_{owner_id}"],
    }
    enter_room = AsyncMock()
    emit = AsyncMock()
    monkeypatch.setattr(websocket_service.sio, "enter_room", enter_room)
    monkeypatch.setattr(websocket_service.sio, "emit", emit)

    await websocket_service.join_room("sid-1", {"room": f"user_{other_id}"})

    enter_room.assert_not_called()
    emit.assert_called_once_with("room_join_denied", {"room": f"user_{other_id}"}, to="sid-1")


@pytest.mark.asyncio
async def test_agent_security_alerts_notify_with_scoped_helper_and_owner_id(monkeypatch):
    user_id = ObjectId()
    watchdog_id = ObjectId()
    alert_id = ObjectId()
    inserted_device_doc = {}

    async def insert_device(doc):
        inserted_device_doc.update(doc)
        return SimpleNamespace(inserted_id=watchdog_id)

    db = MagicMock()
    db.devices.find = MagicMock(return_value=FakeCursor([]))
    db.devices.insert_one = AsyncMock(side_effect=insert_device)
    db.alerts.find_one = AsyncMock(return_value=None)
    db.alerts.insert_one = AsyncMock(return_value=SimpleNamespace(inserted_id=alert_id))
    monkeypatch.setattr(agent_security_routes, "get_database", AsyncMock(return_value=db))
    send_notifications = AsyncMock()
    monkeypatch.setattr(agent_security_routes, "send_alert_notifications", send_notifications)

    request = MagicMock()
    request.json = AsyncMock(return_value={
        "dns_changed": True,
        "dns_servers": ["8.8.8.8"],
        "expected_dns": ["1.1.1.1"],
        "unknown_ips": [],
    })

    response = await agent_security_routes.receive_security_report(
        request,
        api_key_user={"_id": user_id, "_family_id": None},
    )

    assert response["ok"] is True
    assert inserted_device_doc["owner_id"] == user_id
    send_notifications.assert_awaited_once_with(
        str(alert_id),
        str(watchdog_id),
        "DNS server changed: expected ['1.1.1.1'], got ['8.8.8.8']",
        "high",
    )
