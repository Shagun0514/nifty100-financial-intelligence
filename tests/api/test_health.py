from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_returns_200_and_ok(api_db):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_health_db_row_counts_present(api_db):
    r = client.get("/api/v1/health")
    body = r.json()
    assert "companies" in body["db_row_counts"]
    assert body["db_row_counts"]["companies"] == 3


def test_health_has_uptime_and_version(api_db):
    r = client.get("/api/v1/health")
    body = r.json()
    assert "uptime_seconds" in body
    assert "version" in body
