"""Regression tests for high-impact tenant/auth security bugs."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from models import UserCreate


def test_public_signup_rejects_admin_role() -> None:
    """Public signup must not allow self-service admin accounts."""
    with pytest.raises(Exception):
        UserCreate(
            name="Mallory",
            email="mallory@example.com",
            password="StrongPass123!",
            role="admin",
        )

    user = UserCreate(
        name="Business User",
        email="business@example.com",
        password="StrongPass123!",
        role="business",
    )
    assert user.role == "business"


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def skip(self, _skip):
        return self

    def limit(self, _limit):
        return self

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, length):
        return self.docs[:length]


@pytest.mark.asyncio
async def test_device_name_search_keeps_user_visibility_scope(monkeypatch) -> None:
    """A name filter must be ANDed with the user/family scope, not replace it."""
    from routes import devices as devices_routes

    db = SimpleNamespace()
    db.devices = MagicMock()
    db.devices.find = MagicMock(return_value=_Cursor([]))
    db.devices.count_documents = AsyncMock(return_value=0)

    monkeypatch.setattr(devices_routes, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr(devices_routes, "_get_user_family_id", AsyncMock(return_value=None))

    user_id = ObjectId()
    await devices_routes.get_devices(
        device_type=None,
        status=None,
        name="Kitchen Cam",
        page=1,
        limit=10,
        user={"_id": user_id},
    )

    query = db.devices.find.call_args.args[0]
    assert "$and" in query
    assert {"$or": [{"userId": user_id}, {"user_id": user_id}], "isDeleted": {"$ne": True}} in query["$and"]
    assert {
        "$or": [
            {"name": {"$regex": "Kitchen\\ Cam", "$options": "i"}},
            {"deviceId": {"$regex": "Kitchen\\ Cam", "$options": "i"}},
        ]
    } in query["$and"]


def test_alert_cleanup_requires_authentication(client: TestClient, mock_db) -> None:
    """Unauthenticated cleanup must not permanently delete alerts."""
    mock_db.alerts = MagicMock()
    mock_db.alerts.delete_many = AsyncMock()

    response = client.delete("/api/alerts/cleanup?days=0")

    assert response.status_code in (401, 403)
    mock_db.alerts.delete_many.assert_not_called()


@pytest.mark.asyncio
async def test_alert_cleanup_deletes_only_current_users_device_alerts(monkeypatch) -> None:
    """Cleanup is scoped to the authenticated user's visible devices."""
    from routes import alerts as alerts_routes

    device_id = ObjectId()
    db = SimpleNamespace()
    db.alerts = MagicMock()
    db.alerts.delete_many = AsyncMock(return_value=SimpleNamespace(deleted_count=2))

    monkeypatch.setattr(alerts_routes, "get_database", AsyncMock(return_value=db))
    monkeypatch.setattr(alerts_routes, "_device_ids_for_user_alerts", AsyncMock(return_value=[device_id]))

    result = await alerts_routes.cleanup_old_alerts(days=30, user={"_id": ObjectId()})

    assert result["deleted_count"] == 2
    query = db.alerts.delete_many.call_args.args[0]
    assert query["$and"][0] == {
        "$or": [
            {"deviceId": {"$in": [device_id]}},
            {"device_id": {"$in": [device_id]}},
        ]
    }
    date_scope = query["$and"][1]["$or"]
    assert set(date_scope[0]["createdAt"].keys()) == {"$lt"}
    assert set(date_scope[1]["created_at"].keys()) == {"$lt"}
    assert isinstance(date_scope[0]["createdAt"]["$lt"], datetime)
