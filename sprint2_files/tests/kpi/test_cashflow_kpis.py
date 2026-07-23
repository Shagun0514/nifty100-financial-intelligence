from src.analytics.cashflow_kpis import (free_cash_flow, cfo_quality_score, capex_intensity,
                                          fcf_conversion_rate, capital_allocation_pattern)


def test_fcf():
    assert free_cash_flow(500, -200) == 300


def test_cfo_quality_high():
    _, label = cfo_quality_score([120, 130, 140], [100, 110, 120])
    assert label == "High Quality"


def test_cfo_quality_accrual_risk():
    _, label = cfo_quality_score([20, 25, 30], [100, 110, 120])
    assert label == "Accrual Risk"


def test_capex_intensity_asset_light():
    pct, label = capex_intensity(-20, 1000)
    assert label == "Asset Light"


def test_capex_intensity_capital_intensive():
    pct, label = capex_intensity(-150, 1000)
    assert label == "Capital Intensive"


def test_fcf_conversion_zero_ebitda_none():
    assert fcf_conversion_rate(100, 0) is None


def test_capital_allocation_reinvestor():
    assert capital_allocation_pattern(500, -300, -100, cfo_over_pat=0.8) == "Reinvestor"


def test_capital_allocation_shareholder_returns():
    assert capital_allocation_pattern(500, -300, -100, cfo_over_pat=1.5) == "Shareholder Returns"


def test_capital_allocation_distress():
    assert capital_allocation_pattern(-100, 50, 80) == "Distress Signal"
