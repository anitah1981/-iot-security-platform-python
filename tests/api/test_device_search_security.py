import re
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from routes import devices as devices_route


class _FakeCursor:
    def __init__(self, documents):
        self._documents = documents
        self._skip = 0
        self._limit = len(documents)

    def skip(self, value):
        self._skip = value
        return self

    def limit(self, value):
        self._limit = value
        return self

    def sort(self, _value):
        return self

    async def to_list(self, length):
        end = self._skip + min(self._limit, length)
        return self._documents[self._skip:end]


def _matches(document, query):
    for key, expected in query.items():
        if key == "$and":
            if not all(_matches(document, item) for item in expected):
                return False
            continue
        if key == "$or":
            if not any(_matches(document, item) for item in expected):
                return False
            continue

        actual = document.get(key)
        if isinstance(expected, dict):
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            if "$regex" in expected:
                if re.search(expected["$regex"], str(actual or ""), re.IGNORECASE if expected.get("$options") == "i" else 0) is None:
                    return False
        elif actual != expected:
            return False
    return True


class _FakeCollection:
    def __init__(self, documents):
        self._documents = documents
        self.last_query = None

    def find(self, query):
        self.last_query = query
        return _FakeCursor([doc for doc in self._documents if _matches(doc, query)])

    async def count_documents(self, query):
        return len([doc for doc in self._documents if _matches(doc, query)])


def _device(owner_id, name):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "user_id": owner_id,
        "deviceId": f"{name.lower().replace(' ', '-')}-{owner_id}",
        "name": name,
        "type": "Camera",
        "status": "online",
        "heartbeatInterval": 30,
        "alertsEnabled": True,
        "isDeleted": False,
        "createdAt": now,
        "updatedAt": now,
    }


@pytest.mark.asyncio
async def test_device_name_search_preserves_user_scope(monkeypatch):
    user_id = ObjectId()
    other_user_id = ObjectId()
    fake_devices = _FakeCollection(
        [
            _device(user_id, "Kitchen Camera"),
            _device(other_user_id, "Kitchen Camera"),
        ]
    )
    fake_db = type(
        "FakeDb",
        (),
        {
            "devices": fake_devices,
            "family_members": type(
                "FakeFamilyMembers",
                (),
                {"find_one": AsyncMock(return_value=None)},
            )(),
        },
    )()
    monkeypatch.setattr(devices_route, "get_database", AsyncMock(return_value=fake_db))

    response = await devices_route.get_devices(name="Kitchen", user={"_id": user_id})

    assert response.total == 1
    assert [device.name for device in response.devices] == ["Kitchen Camera"]
    assert "$and" in fake_devices.last_query
