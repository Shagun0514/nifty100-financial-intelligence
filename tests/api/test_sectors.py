from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_sectors_returns_all_sectors(api_db):
    r = client.get("/api/v1/sectors")
    assert r.status_code == 200
    names = {s["sector"] for s in r.json()}
    assert "Information Technology" in names
    assert "Financials" in names


def test_sector_companies_filters_correctly(api_db):
    r = client.get("/api/v1/sectors/Information Technology/companies")
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()}
    assert ids == {"TCS", "INFY"}


def test_sector_unknown_returns_404(api_db):
    r = client.get("/api/v1/sectors/NotASector/companies")
    assert r.status_code == 404
