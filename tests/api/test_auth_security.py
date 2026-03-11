"""Auth security automation: login rate limit regression."""
from typing import Dict, Any

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock


def _setup_mock_user_collection_for_login(mock_db, user: Dict[str, Any] | None) -> None:
    """
    Patch the users collection so login can run without a real DB.
    find_one MUST be AsyncMock so 'await db.users.find_one(...)' works.
    """
    users = MagicMock()
    users.find_one = AsyncMock(return_value=user)
    users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_db.users = users
    # Audit logger inserts must not raise
    audit = MagicMock()
    audit.insert_one = AsyncMock(return_value=None)
    mock_db.audit_logs = audit


def test_login_returns_401_for_unknown_user(client: TestClient, mock_db) -> None:
    """Regression: login with unknown email returns 401 (no 500)."""
    _setup_mock_user_collection_for_login(mock_db, user=None)
    r = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "any"},
    )
    assert r.status_code == 401


