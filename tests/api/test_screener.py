from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_screener_min_roe_filters_correctly(api_db):
    r = client.get("/api/v1/screener?min_roe=15")
    assert r.status_code == 200
    results = r.json()
    assert all(c["return_on_equity_pct"] >= 15 for c in results)
    # TCS(30) and INFY(20) pass, HDFCBANK(10) does not
    tickers = {c["company_id"] for c in results}
    assert "TCS" in tickers and "INFY" in tickers
    assert "HDFCBANK" not in tickers


def test_screener_invalid_param_returns_400(api_db):
    r = client.get("/api/v1/screener?min_roe=notanumber")
    assert r.status_code == 400


def test_screener_no_filters_returns_all(api_db):
    r = client.get("/api/v1/screener")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_screener_de_max_skips_financials(api_db):
    r = client.get("/api/v1/screener?max_de=0.1")
    tickers = {c["company_id"] for c in r.json()}
    # HDFCBANK (Financials) has DE=0.5 > 0.1 but should still pass since it's skipped
    assert "HDFCBANK" in tickers
