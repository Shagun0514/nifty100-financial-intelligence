import math
from src.analytics.ratios import (
    net_profit_margin, operating_profit_margin, return_on_equity,
    return_on_capital_employed, return_on_assets, debt_to_equity,
    interest_coverage, net_debt, asset_turnover,
)

# --- Day 08: profitability ---

def test_npm_normal():
    assert net_profit_margin(150, 1000) == 15.0


def test_npm_zero_sales_none():
    assert net_profit_margin(100, 0) is None


def test_opm_cross_check_match():
    val, mismatch = operating_profit_margin(210, 1000, opm_percentage=21.0)
    assert val == 21.0 and mismatch is False


def test_opm_cross_check_mismatch():
    val, mismatch = operating_profit_margin(210, 1000, opm_percentage=25.0)
    assert mismatch is True


def test_roe_normal():
    assert return_on_equity(100, 400, 100) == 20.0


def test_roe_negative_equity_none():
    assert return_on_equity(100, -50, 0) is None


def test_roce_normal():
    # EBIT = 300-50=250, capital=400+100+200=700 -> 250/700*100
    assert math.isclose(return_on_capital_employed(300, 50, 400, 100, 200), 250 / 700 * 100)


def test_roa_zero_assets_none():
    assert return_on_assets(100, 0) is None


# --- Day 09: leverage & efficiency ---

def test_de_debt_free_returns_zero():
    de, flag = debt_to_equity(0, 500, 100)
    assert de == 0.0 and flag is False


def test_de_high_leverage_flag_non_financial():
    de, flag = debt_to_equity(3000, 400, 100)  # DE = 6 > 5
    assert flag is True


def test_de_high_leverage_suppressed_for_financials():
    de, flag = debt_to_equity(3000, 400, 100, sector="Financials")
    assert flag is False


def test_icr_interest_zero_none_and_debt_free_label():
    icr, label, risk = interest_coverage(500, 50, 0)
    assert icr is None and label == "Debt Free" and risk is False


def test_icr_normal():
    icr, label, risk = interest_coverage(500, 50, 100)
    assert math.isclose(icr, 5.5)


def test_icr_at_risk_flag():
    icr, label, risk = interest_coverage(100, 0, 100)  # icr=1.0 < 1.5
    assert risk is True


def test_net_debt():
    assert net_debt(1000, 300) == 700


def test_asset_turnover_zero_assets_none():
    assert asset_turnover(1000, 0) is None


def test_asset_turnover_normal():
    assert asset_turnover(1000, 500) == 2.0
