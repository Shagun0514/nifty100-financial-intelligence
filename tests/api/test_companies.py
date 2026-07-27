from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_companies_returns_all(api_db):
    r = client.get("/api/v1/companies")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_companies_ticker_returns_correct_data(api_db):
    r = client.get("/api/v1/companies/TCS")
    assert r.status_code == 200
    assert r.json()["id"] == "TCS"
    assert r.json()["company_name"] == "Tata Consultancy"


def test_companies_invalid_ticker_404(api_db):
    r = client.get("/api/v1/companies/INVALID")
    assert r.status_code == 404


def test_companies_sector_filter(api_db):
    r = client.get("/api/v1/companies?sector=Financials")
    assert r.status_code == 200
    assert all(c["broad_sector"] == "Financials" for c in r.json())


def test_companies_search_filter(api_db):
    r = client.get("/api/v1/companies?search=TCS")
    assert r.status_code == 200
    assert any(c["id"] == "TCS" for c in r.json())


def test_companies_pl_history(api_db):
    r = client.get("/api/v1/companies/TCS/pl")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_companies_ratios(api_db):
    r = client.get("/api/v1/companies/TCS/ratios")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_companies_ratios_single_year(api_db):
    r = client.get("/api/v1/companies/TCS/ratios?year=2023-03")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_companies_tearsheet_404_when_missing(api_db):
    # Use a ticker with no possible tearsheet file, rather than TCS - a real project
    # directory may already have reports/tearsheets/TCS_tearsheet.pdf from Sprint 5.
    r = client.get("/api/v1/companies/ZZZ_NO_SUCH_TICKER_EVER/tearsheet")
    assert r.status_code == 404


def test_companies_documents(api_db):
    r = client.get("/api/v1/companies/TCS/documents")
    assert r.status_code == 200
    assert r.json()[0]["is_url_valid"] is True
