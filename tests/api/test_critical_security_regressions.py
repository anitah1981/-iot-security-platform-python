from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from models import AlertCreate, UserCreate


class AsyncCursor:
    def __init__(self, docs):
        self.docs = docs

    def skip(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def sort(self, *_args):
        return self

    async def to_list(self, length=None):
        return self.docs if length is None else self.docs[:length]


class CapturingCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.find_queries = []
        self.delete_queries = []
        self.inserted_docs = []

    def find(self, query=None):
        self.find_queries.append(query or {})
        return AsyncCursor(self.docs)

    async def find_one(self, query=None):
        self.find_queries.append(query or {})
        return self.docs[0] if self.docs else None

    async def count_documents(self, query):
        self.find_queries.append(query)
        return len(self.docs)

    async def delete_many(self, query):
        self.delete_queries.append(query)
        return SimpleNamespace(deleted_count=1)

    async def insert_one(self, doc):
        self.inserted_docs.append(doc)
        return SimpleNamespace(inserted_id=ObjectId())


def test_public_signup_rejects_admin_role():
    with pytest.raises(ValidationError):
        UserCreate(
            name="Mallory",
            email="mallory@example.com",
            password="Str0ng!Password",
            role="admin",
        )


def test_alert_create_and_cleanup_require_auth(client: TestClient):
    device_id = str(ObjectId())

    create_response = client.post(
        "/api/alerts",
        json={
            "device_id": device_id,
            "message": "Injected alert",
            "severity": "critical",
            "type": "security",
        },
    )
    cleanup_response = client.delete("/api/alerts/cleanup?days=1")

    assert create_response.status_code in (401, 403)
    assert cleanup_response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_device_name_search_preserves_user_scope(monkeypatch):
    import routes.devices as devices_route

    user_id = ObjectId()
    devices_collection = CapturingCollection()
    db = SimpleNamespace(devices=devices_collection)
    monkeypatch.setattr(devices_route, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr(devices_route, "_get_user_family_id", AsyncMock(return_value=None))

    await devices_route.get_devices(name="camera.*", user={"_id": user_id})

    query = devices_collection.find_queries[0]
    assert "$and" in query
    assert {"$or": [{"userId": user_id}, {"user_id": user_id}]} in query["$and"]
    assert {"isDeleted": {"$ne": True}} in query["$and"]

    search_filter = next(item for item in query["$and"] if item.get("$or") and "name" in item["$or"][0])
    assert search_filter["$or"][0]["name"]["$regex"] == r"camera\.\*"


@pytest.mark.asyncio
async def test_alert_cleanup_deletes_only_current_user_devices(monkeypatch):
    import routes.alerts as alerts_route

    user_id = ObjectId()
    device_id = ObjectId()
    devices_collection = CapturingCollection([{"_id": device_id, "userId": user_id}])
    alerts_collection = CapturingCollection()
    db = SimpleNamespace(devices=devices_collection, alerts=alerts_collection)
    monkeypatch.setattr(alerts_route, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr(alerts_route, "_get_user_family_id", AsyncMock(return_value=None))

    response = await alerts_route.cleanup_old_alerts(days=7, user={"_id": user_id})

    assert response["deleted_count"] == 1
    delete_query = alerts_collection.delete_queries[0]
    device_scope = delete_query["$and"][0]["$or"]
    assert {"deviceId": {"$in": [device_id]}} in device_scope
    assert {"device_id": {"$in": [device_id]}} in device_scope


@pytest.mark.asyncio
async def test_alert_create_rejects_foreign_device(monkeypatch):
    import routes.alerts as alerts_route

    user_id = ObjectId()
    foreign_device_id = ObjectId()
    devices_collection = CapturingCollection([])
    alerts_collection = CapturingCollection()
    db = SimpleNamespace(devices=devices_collection, alerts=alerts_collection)
    monkeypatch.setattr(alerts_route, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr(alerts_route, "_get_user_family_id", AsyncMock(return_value=None))

    alert = AlertCreate(
        device_id=str(foreign_device_id),
        message="Foreign device alert",
        severity="critical",
        type="security",
    )

    with pytest.raises(HTTPException) as exc:
        await alerts_route.create_alert(alert, BackgroundTasks(), user={"_id": user_id})

    assert exc.value.status_code == 403
    assert alerts_collection.inserted_docs == []


@pytest.mark.asyncio
async def test_alert_notifications_target_device_owner_and_family(monkeypatch):
    import routes.alerts as alerts_route

    owner_id = ObjectId()
    family_member_id = ObjectId()
    outsider_id = ObjectId()
    family_id = ObjectId()
    device_id = ObjectId()
    users = [
        {"_id": owner_id, "email": "owner@example.com", "name": "Owner"},
        {"_id": family_member_id, "email": "family@example.com", "name": "Family"},
        {"_id": outsider_id, "email": "outsider@example.com", "name": "Outsider"},
    ]

    class UsersCollection(CapturingCollection):
        def find(self, query=None):
            self.find_queries.append(query or {})
            allowed = set(query["_id"]["$in"])
            return AsyncCursor([user for user in users if user["_id"] in allowed])

    db = SimpleNamespace(
        devices=CapturingCollection([{"_id": device_id, "name": "Doorbell", "userId": owner_id, "family_id": family_id}]),
        family_members=CapturingCollection([
            {"family_id": family_id, "user_id": owner_id},
            {"family_id": family_id, "user_id": family_member_id},
        ]),
        users=UsersCollection(users),
        notification_preferences=CapturingCollection([]),
    )
    sent_to = []

    async def fake_send_alert_notification(**kwargs):
        sent_to.append(kwargs["user_email"])
        return []

    monkeypatch.setattr(alerts_route, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr("services.notification_service.send_alert_notification", fake_send_alert_notification)

    await alerts_route.send_alert_notifications(
        alert_id=str(ObjectId()),
        device_id=str(device_id),
        alert_message="Motion detected",
        alert_severity="high",
    )

    assert sent_to == ["owner@example.com", "family@example.com"]
