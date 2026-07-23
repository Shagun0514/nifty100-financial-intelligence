"""Profitability, leverage, and efficiency ratio formulas — Sprint 2, Day 08-09.

Every function is a pure function on plain numbers so it's trivially unit-testable;
src/analytics/populate_ratios.py wires these to the actual database rows.
"""
from typing import Optional, Tuple


def net_profit_margin(net_profit: float, sales: float) -> Optional[float]:
    """net_profit / sales * 100. None if sales == 0."""
    if not sales:
        return None
    return net_profit / sales * 100


def operating_profit_margin(operating_profit: float, sales: float,
                             opm_percentage: Optional[float] = None,
                             tolerance: float = 1.0) -> Tuple[Optional[float], bool]:
    """Computed OPM% and a mismatch flag vs the source opm_percentage field (>1% diff)."""
    if not sales:
        return None, False
    computed = operating_profit / sales * 100
    mismatch = opm_percentage is not None and abs(computed - opm_percentage) > tolerance
    return computed, mismatch


def return_on_equity(net_profit: float, equity_capital: float, reserves: float) -> Optional[float]:
    """ROE = net_profit / (equity + reserves) * 100. None if equity+reserves <= 0."""
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0:
        return None
    return net_profit / equity * 100


def return_on_capital_employed(operating_profit: float, depreciation: float,
                                equity_capital: float, reserves: float, borrowings: float,
                                sector: Optional[str] = None) -> Optional[float]:
    """ROCE = EBIT / (equity + reserves + borrowings) * 100.
    EBIT = operating_profit - depreciation.
    For Financials sector, this is still computed but should be read against a
    sector-relative benchmark rather than the universal threshold (see populate_ratios.py)."""
    ebit = (operating_profit or 0) - (depreciation or 0)
    capital_employed = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital_employed <= 0:
        return None
    return ebit / capital_employed * 100


def return_on_assets(net_profit: float, total_assets: float) -> Optional[float]:
    """ROA = net_profit / total_assets * 100. None if total_assets == 0."""
    if not total_assets:
        return None
    return net_profit / total_assets * 100


def debt_to_equity(borrowings: float, equity_capital: float, reserves: float,
                    sector: Optional[str] = None) -> Tuple[float, bool]:
    """D/E = borrowings / (equity+reserves). Returns 0 (not None) if borrowings == 0.
    high_leverage_flag is True if D/E > 5 AND sector is not Financials."""
    equity = (equity_capital or 0) + (reserves or 0)
    if not borrowings:
        return 0.0, False
    if equity <= 0:
        return float("inf"), (sector != "Financials")
    de = borrowings / equity
    high_leverage = de > 5 and sector != "Financials"
    return de, high_leverage


def interest_coverage(operating_profit: float, other_income: float,
                       interest: float) -> Tuple[Optional[float], str, bool]:
    """ICR = (operating_profit + other_income) / interest.
    Returns (value, label, at_risk_flag).
    interest == 0 -> (None, 'Debt Free', False).
    at_risk_flag True if 0 < ICR < 1.5."""
    if not interest:
        return None, "Debt Free", False
    icr = ((operating_profit or 0) + (other_income or 0)) / interest
    at_risk = icr < 1.5
    return icr, "", at_risk


def net_debt(borrowings: float, investments: float) -> float:
    """Net Debt = borrowings - investments (investments used as liquid-asset proxy)."""
    return (borrowings or 0) - (investments or 0)


def asset_turnover(sales: float, total_assets: float) -> Optional[float]:
    """Asset Turnover = sales / total_assets. None if total_assets == 0."""
    if not total_assets:
        return None
    return sales / total_assets
