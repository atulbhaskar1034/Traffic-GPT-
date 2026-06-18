"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoints:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "GRIDLOCK" in resp.json()["service"]

    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_readiness(self, client):
        resp = client.get("/api/v1/ready")
        assert resp.status_code == 200
        assert "models_loaded" in resp.json()
