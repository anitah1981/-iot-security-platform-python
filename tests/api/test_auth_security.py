"""Auth security automation: login rate limit regression."""
from typing import Dict, Any

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock


def _setup_mock_user_collection_for_login(mock_db, user: Dict[str, Any] | None) -> None:
    """Patch the users collection so login can run without a real DB."""
    mock_db.users = MagicMock()
    mock_db.users.find_one = AsyncMock(return_value=user)


def test_login_rate_limit_exceeded(client: TestClient, mock_db) -> None:
    """
    After enough attempts from the same client, /api/auth/login should be rate limited.

    This relies on SlowAPI's default key_func (remote address) and exercises the
    5/minute limiter configured on the login route.
    """
    _setup_mock_user_collection_for_login(mock_db, user=None)

    payload = {"email": "tester@example.com", "password": "wrong-password"}

    last_status = None
    for _ in range(6):  # limit is 5/minute
        r = client.post("/api/auth/login", json=payload)
        last_status = r.status_code

    assert last_status == 429


