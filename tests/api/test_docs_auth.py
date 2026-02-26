"""Security regression: /docs and /redoc require authentication."""
import pytest
from fastapi.testclient import TestClient


def test_docs_requires_auth(client: TestClient):
    r = client.get("/docs")
    assert r.status_code in (401, 403, 307), "/docs should not be public (401/403 or redirect to login)"


def test_redoc_requires_auth(client: TestClient):
    r = client.get("/redoc")
    assert r.status_code in (401, 403, 307), " /redoc should not be public"
