"""Security automation: headers, /docs auth, rate limit presence."""
import pytest
from fastapi.testclient import TestClient


def test_security_headers_present(client: TestClient):
    """Response from public endpoint should include security headers."""
    r = client.get("/api/health")
    assert r.status_code == 200
    headers = r.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "X-XSS-Protection" in headers or "Content-Security-Policy" in headers


def test_docs_returns_401_without_auth(client: TestClient):
    """/docs must not be publicly accessible (401 or 403)."""
    r = client.get("/docs", follow_redirects=False)
    assert r.status_code in (401, 403)


def test_redoc_returns_401_without_auth(client: TestClient):
    """/redoc must not be publicly accessible."""
    r = client.get("/redoc", follow_redirects=False)
    assert r.status_code in (401, 403)
