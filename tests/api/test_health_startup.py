"""API tests for /api/health, /api/startup, /api/ready (no auth)."""
import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data.get("status") == "alive"
    assert "timestamp" in data


def test_startup(client: TestClient):
    r = client.get("/api/startup")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "tasks" in data
    assert isinstance(data["tasks"], dict)
    assert "timestamp" in data
    # When lifespan runs (e.g. real server), tasks are populated; TestClient may not run lifespan
    if data["tasks"]:
        assert "database" in data["tasks"] or "heartbeat_sweep" in data["tasks"]


def test_ready(client: TestClient):
    r = client.get("/api/ready")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data.get("database") == "connected"
