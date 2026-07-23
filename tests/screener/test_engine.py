import pandas as pd
from src.screener.engine import apply_filters, winsor_scale, compute_composite_scores, _passes


def _sample_df():
    return pd.DataFrame({
        "company_id": ["A", "B", "C", "D"],
        "broad_sector": ["IT", "Financials", "IT", "FMCG"],
        "return_on_equity_pct": [20, 8, 30, 12],
        "return_on_capital_employed_pct": [25, 10, 35, 15],
        "net_profit_margin_pct": [18, 6, 22, 10],
        "debt_to_equity": [0.2, 6.0, 0.0, 1.2],
        "interest_coverage": [10, None, None, 3],  # B has interest but low ICR-ish; C is Debt Free
        "free_cash_flow_cr": [500, -50, 800, 100],
        "cfo_quality_score": [1.2, 0.4, 1.5, 0.9],
        "revenue_cagr_5yr": [15, 5, 20, 8],
        "pat_cagr_5yr": [18, 3, 25, 6],
    })


def test_de_max_skips_financials():
    df = _sample_df()
    result = apply_filters(df, {"de_max": 1.0})
    # B is Financials with DE=6 > 1.0 but should still pass because it's skipped
    assert "B" in result["company_id"].values
    # D is not Financials, DE=1.2 > 1.0 -> excluded
    assert "D" not in result["company_id"].values


def test_icr_min_treats_none_as_infinity():
    df = _sample_df()
    result = apply_filters(df, {"icr_min": 5})
    # C has ICR=None (Debt Free) -> should pass any threshold
    assert "C" in result["company_id"].values
    # D has ICR=3 < 5 -> excluded
    assert "D" not in result["company_id"].values


def test_roe_min_filter():
    df = _sample_df()
    result = apply_filters(df, {"roe_min": 15})
    assert set(result["company_id"]) == {"A", "C"}


def test_winsor_scale_range():
    s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    scaled = winsor_scale(s)
    assert scaled.min() >= 0 and scaled.max() <= 100


def test_composite_score_higher_for_better_company():
    df = _sample_df()
    scores = compute_composite_scores(df, sector_relative=False)
    # C has best ROE, ROCE, NPM, lowest debt, highest FCF -> should score highest
    c_score = scores[df["company_id"] == "C"].iloc[0]
    b_score = scores[df["company_id"] == "B"].iloc[0]
    assert c_score > b_score


def test_passes_min_and_max():
    assert _passes("roe_min", 20, 15) is True
    assert _passes("roe_min", 10, 15) is False
    assert _passes("pe_max", 15, 20) is True
    assert _passes("pe_max", 25, 20) is False


def test_passes_missing_value_fails():
    assert _passes("roe_min", float("nan"), 15) is False
