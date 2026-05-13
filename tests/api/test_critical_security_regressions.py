"""Regression tests for high-impact auth and tenancy bugs."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pydantic import ValidationError

from models import UserCreate


class _FakeCursor:
    def __init__(self, docs=None):
        self.docs = docs or []

    def skip(self, _value):
        return self

    def limit(self, _value):
        return self

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, length):
        return self.docs[:length]


def test_public_signup_cannot_request_admin_role():
    with pytest.raises(ValidationError):
        UserCreate(
            name="Mallory",
            email="mallory@example.com",
            password="StrongPassw0rd!",
            role="admin",
        )


@pytest.mark.asyncio
async def test_device_search_keeps_user_scope(monkeypatch):
    from routes import devices as devices_routes

    user_id = ObjectId()
    db = SimpleNamespace(
        family_members=SimpleNamespace(find_one=AsyncMock(return_value=None)),
        devices=SimpleNamespace(
            find=MagicMock(return_value=_FakeCursor([])),
            count_documents=AsyncMock(return_value=0),
        ),
    )
    monkeypatch.setattr(devices_routes, "get_database", AsyncMock(return_value=db))

    await devices_routes.get_devices(
        device_type=None,
        status=None,
        name="Kitchen (Main)",
        page=1,
        limit=10,
        user={"_id": user_id},
    )

    query = db.devices.find.call_args.args[0]
    assert "$or" not in query
    assert query["isDeleted"] == {"$ne": True}
    assert {"$or": [{"userId": user_id}, {"user_id": user_id}]} in query["$and"]
    assert {
        "$or": [
            {"name": {"$regex": r"Kitchen\ \(Main\)", "$options": "i"}},
            {"deviceId": {"$regex": r"Kitchen\ \(Main\)", "$options": "i"}},
            {"device_id": {"$regex": r"Kitchen\ \(Main\)", "$options": "i"}},
        ]
    } in query["$and"]


def test_alert_cleanup_requires_auth(client: TestClient, mock_db):
    mock_db.alerts = SimpleNamespace(
        delete_many=AsyncMock(return_value=SimpleNamespace(deleted_count=1))
    )

    response = client.delete("/api/alerts/cleanup?days=30")

    assert response.status_code in (401, 403)
    mock_db.alerts.delete_many.assert_not_called()


@pytest.mark.asyncio
async def test_alert_cleanup_deletes_only_current_users_alerts(monkeypatch):
    from routes import alerts as alerts_routes

    user_id = ObjectId()
    device_id = ObjectId()
    delete_result = SimpleNamespace(deleted_count=2)
    db = SimpleNamespace(
        family_members=SimpleNamespace(find_one=AsyncMock(return_value=None)),
        devices=SimpleNamespace(find=MagicMock(return_value=_FakeCursor([{"_id": device_id}]))),
        alerts=SimpleNamespace(delete_many=AsyncMock(return_value=delete_result)),
    )
    monkeypatch.setattr(alerts_routes, "get_database", AsyncMock(return_value=db))

    response = await alerts_routes.cleanup_old_alerts(days=30, user={"_id": user_id})

    assert response["deleted_count"] == 2
    delete_query = db.alerts.delete_many.call_args.args[0]
    assert {
        "$or": [
            {"deviceId": {"$in": [device_id]}},
            {"device_id": {"$in": [device_id]}},
        ]
    } in delete_query["$and"]
    assert db.devices.find.call_args.args[0] == {
        "$or": [{"userId": user_id}, {"user_id": user_id}],
        "isDeleted": {"$ne": True},
    }
