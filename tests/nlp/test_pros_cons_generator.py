import pandas as pd
from src.nlp.pros_cons_generator import generate_pros_cons_for_company, CONFIDENCE_THRESHOLD


def _base_hist(n=6, **overrides):
    data = {
        "return_on_equity_pct": [22] * n, "return_on_capital_employed_pct": [15] * n,
        "debt_to_equity": [0] * n, "free_cash_flow_cr": [100] * n,
        "revenue_cagr_5yr": [10] * n, "pat_cagr_5yr": [8] * n, "eps_cagr_5yr": [5] * n,
        "operating_profit_margin_pct": [18] * n, "interest_coverage": [8] * n,
        "icr_label": [""] * n, "dividend_payout_ratio_pct": [10] * n,
        "total_debt_cr": [0] * n, "sales": [1000] * n, "net_profit": [100] * n,
        "total_assets": [1000] * n, "borrowings": [0] * n, "earnings_per_share": [10] * n,
        "ebitda_proxy": [200] * n,
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_pro03_debt_free():
    hist = _base_hist(de=None)
    hist["debt_to_equity"] = 0.0
    entries = generate_pros_cons_for_company(hist, "Information Technology")
    assert any(e["rule_id"] == "PRO-03" for e in entries)


def test_pro01_high_sustained_roe():
    hist = _base_hist()
    hist["return_on_equity_pct"] = [22, 22, 22, 22, 22, 22]
    entries = generate_pros_cons_for_company(hist, "IT")
    assert any(e["rule_id"] == "PRO-01" for e in entries)


def test_con04_net_loss():
    hist = _base_hist()
    hist.loc[hist.index[-1], "net_profit"] = -50
    entries = generate_pros_cons_for_company(hist, "IT")
    assert any(e["rule_id"] == "CON-04" for e in entries)


def test_con01_high_leverage_non_financial():
    hist = _base_hist()
    hist["debt_to_equity"] = [3.0] * 6
    entries = generate_pros_cons_for_company(hist, "Industrials")
    assert any(e["rule_id"] == "CON-01" for e in entries)


def test_con01_suppressed_for_financials():
    hist = _base_hist()
    hist["debt_to_equity"] = [3.0] * 6
    entries = generate_pros_cons_for_company(hist, "Financials")
    assert not any(e["rule_id"] == "CON-01" for e in entries)


def test_con06_low_icr():
    hist = _base_hist()
    hist["interest_coverage"] = [1.0] * 6
    hist["icr_label"] = [""] * 6
    entries = generate_pros_cons_for_company(hist, "IT")
    assert any(e["rule_id"] == "CON-06" for e in entries)


def test_con07_excessive_payout():
    hist = _base_hist()
    hist["dividend_payout_ratio_pct"] = [150] * 6
    entries = generate_pros_cons_for_company(hist, "IT")
    assert any(e["rule_id"] == "CON-07" for e in entries)


def test_con10_low_roce():
    hist = _base_hist()
    hist["return_on_capital_employed_pct"] = [5] * 6
    entries = generate_pros_cons_for_company(hist, "IT")
    assert any(e["rule_id"] == "CON-10" for e in entries)


def test_empty_history_returns_empty():
    assert generate_pros_cons_for_company(pd.DataFrame(), "IT") == []


def test_all_confidence_scores_above_threshold():
    hist = _base_hist()
    hist["debt_to_equity"] = [3.0] * 6
    entries = generate_pros_cons_for_company(hist, "Industrials")
    assert all(e["confidence_pct"] > CONFIDENCE_THRESHOLD for e in entries)
