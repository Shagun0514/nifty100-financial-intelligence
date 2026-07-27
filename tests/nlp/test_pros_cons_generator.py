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


def test_all_thresholded_entries_above_threshold():
    """Entries NOT flagged below_threshold must genuinely exceed the confidence cutoff."""
    hist = _base_hist()
    hist["debt_to_equity"] = [3.0] * 6
    entries = generate_pros_cons_for_company(hist, "Industrials")
    for e in entries:
        if not e["below_threshold"]:
            assert e["confidence_pct"] > CONFIDENCE_THRESHOLD


def test_guaranteed_coverage_backfills_missing_con():
    """A very strong company that triggers no genuine 'con' rule still gets one con,
    backfilled from the fallback signal and clearly flagged below_threshold=True."""
    hist = _base_hist()
    # tuned to be uniformly excellent: shouldn't naturally trigger any CON-* rule
    entries = generate_pros_cons_for_company(hist, "Information Technology")
    cons = [e for e in entries if e["type"] == "con"]
    assert len(cons) >= 1
    assert any(e["below_threshold"] for e in cons)


def test_guaranteed_coverage_every_company_has_pro_and_con():
    hist = _base_hist()
    hist["debt_to_equity"] = [3.0] * 6  # push it toward triggering real cons too
    entries = generate_pros_cons_for_company(hist, "Industrials")
    types_present = {e["type"] for e in entries}
    assert "pro" in types_present and "con" in types_present
