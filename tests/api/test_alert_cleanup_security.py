"""Regression tests for alert cleanup authorization and scoping."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from routes.alerts import cleanup_old_alerts


class _AsyncCursor:
    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, length=None):
        return self._docs


def test_alert_cleanup_requires_auth(client: TestClient, mock_db) -> None:
    response = client.delete("/api/alerts/cleanup?days=30")

    assert response.status_code in (401, 403)
    assert not getattr(mock_db.alerts, "delete_many", MagicMock()).called


@pytest.mark.asyncio
async def test_alert_cleanup_deletes_only_current_users_device_alerts() -> None:
    user_id = ObjectId()
    device_id = ObjectId()

    db = MagicMock()
    db.family_members.find_one = AsyncMock(return_value=None)
    db.devices.find = MagicMock(return_value=_AsyncCursor([{"_id": device_id}]))
    db.alerts.delete_many = AsyncMock(return_value=MagicMock(deleted_count=1))

    with patch("routes.alerts.get_database", new_callable=AsyncMock, return_value=db):
        result = await cleanup_old_alerts(days=30, user={"_id": user_id})

    assert result["deleted_count"] == 1
    db.alerts.delete_many.assert_awaited_once()
    delete_query = db.alerts.delete_many.await_args.args[0]
    assert delete_query["$or"] == [
        {"deviceId": {"$in": [device_id]}},
        {"device_id": {"$in": [device_id]}},
    ]
    assert "createdAt" in delete_query
    assert "_id" not in delete_query
