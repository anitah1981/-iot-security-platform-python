"""API route tests: ensure protected routes don't redirect (307) and preserve auth."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


# Routes that must NOT return 307 (redirect) - redirects can strip Authorization header
NO_REDIRECT_PATHS = [
    "/api/devices",
    "/api/alerts",
]


@pytest.mark.parametrize("path", NO_REDIRECT_PATHS)
def test_protected_routes_no_redirect(client: TestClient, path: str):
    """
    Protected API routes must not redirect (307).
    A 307 on /api/devices or /api/alerts causes clients to re-request with a new URL;
    some clients drop Authorization on redirect, leading to 403 Forbidden.
    """
    r = client.get(f"{path}?limit=5&page=1", follow_redirects=False)
    # 401 = auth required (correct, no redirect)
    # 307 = redirect (bad - would strip auth)
    assert r.status_code != 307, (
        f"{path} must not redirect (307). Use @router.get('') not @router.get('/'). "
        "See docs/API_CONVENTIONS.md"
    )
    assert r.status_code in (401, 403), f"{path} should return 401/403 when unauthenticated, got {r.status_code}"


def test_health_no_redirect(client: TestClient):
    """Public /api/health must not redirect."""
    r = client.get("/api/health", follow_redirects=False)
    assert r.status_code == 200
    assert r.status_code != 307


def test_alert_cleanup_requires_auth(client: TestClient, mock_db):
    """Anonymous callers must not be able to trigger destructive alert cleanup."""
    mock_db.alerts = MagicMock()

    r = client.delete("/api/alerts/cleanup?days=0")

    assert r.status_code in (401, 403)
    assert not mock_db.alerts.delete_many.called


def test_alert_cleanup_requires_admin(client: TestClient, mock_db):
    """Authenticated non-admin users must not be able to delete alert history."""
    mock_db.alerts = MagicMock()
    user = {"_id": "507f1f77bcf86cd799439011", "role": "consumer", "email_verified": True}

    with patch("routes.auth._user_from_access_token_string", return_value=user):
        r = client.delete("/api/alerts/cleanup?days=0", headers={"Authorization": "Bearer token"})

    assert r.status_code == 403
    assert not mock_db.alerts.delete_many.called
