"""Tests to ensure core API routes do not redirect (prevents auth-header drop on 307)."""
from fastapi.testclient import TestClient


def test_devices_no_redirect(client: TestClient):
    """GET /api/devices must not 307 redirect (would strip Authorization)."""
    r = client.get("/api/devices")
    assert r.status_code in (200, 401, 403), "Expected 200/401/403, not redirect"
    assert not r.is_redirect, "Must not redirect; redirects can drop Authorization header"


def test_alerts_no_redirect(client: TestClient):
    """GET /api/alerts must not 307 redirect (would strip Authorization)."""
    r = client.get("/api/alerts")
    assert r.status_code in (200, 401, 403), "Expected 200/401/403, not redirect"
    assert not r.is_redirect, "Must not redirect; redirects can drop Authorization header"
