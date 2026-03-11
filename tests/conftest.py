"""
Pytest fixtures. Patches database so API tests can run without a real MongoDB.
"""
import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def env_local(monkeypatch):
    """Use local env for tests so production checks and HTTPS redirect are skipped."""
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("JWT_SECRET", "test-secret-not-for-prod")


@pytest.fixture
def mock_db():
    """Fake database that responds to ping."""
    db = MagicMock()
    db.command = AsyncMock(return_value={"ok": 1})
    # Auth routes await db.users.find_one — must be AsyncMock or login tests fail
    users = MagicMock()
    users.find_one = AsyncMock(return_value=None)
    users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    db.users = users
    audit = MagicMock()
    audit.insert_one = AsyncMock(return_value=None)
    db.audit_logs = audit
    return db


@pytest.fixture
def client(mock_db):
    """TestClient with database mocked so app starts without MongoDB."""
    with patch("database.init_db", new_callable=AsyncMock):
        with patch("database.get_database", new_callable=AsyncMock, return_value=mock_db):
            from main import app
            yield TestClient(app)
