"""CAGR engine — Sprint 2, Day 10. Handles all 6 edge cases from the spec's decision table."""
from typing import Optional, Tuple

DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
TURNAROUND = "TURNAROUND"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


def compute_cagr(start: Optional[float], end: Optional[float], n: int,
                  years_available: Optional[int] = None) -> Tuple[Optional[float], Optional[str]]:
    """CAGR = ((end/start)^(1/n) - 1) * 100.

    Returns (value, flag). flag is None for a normally-computed value, otherwise
    one of DECLINE_TO_LOSS / TURNAROUND / BOTH_NEGATIVE / ZERO_BASE / INSUFFICIENT
    and value is None in every flagged case.
    """
    if years_available is not None and years_available < n:
        return None, INSUFFICIENT
    if start is None or end is None:
        return None, INSUFFICIENT
    if start == 0:
        return None, ZERO_BASE
    if start > 0 and end < 0:
        return None, DECLINE_TO_LOSS
    if start < 0 and end > 0:
        return None, TURNAROUND
    if start < 0 and end < 0:
        return None, BOTH_NEGATIVE
    cagr = ((end / start) ** (1 / n) - 1) * 100
    return cagr, None


def _series_cagr(series: dict, year_now: str, n: int) -> Tuple[Optional[float], Optional[str]]:
    """series keys are 'YYYY-MM' strings, sorted chronologically. Looks up the value
    n entries before year_now in that sorted order."""
    years_sorted = sorted(series.keys())
    if year_now not in years_sorted:
        return None, INSUFFICIENT
    idx_now = years_sorted.index(year_now)
    idx_start = idx_now - n
    if idx_start < 0:
        return None, INSUFFICIENT
    start_year = years_sorted[idx_start]
    return compute_cagr(series[start_year], series[year_now], n)


def revenue_cagr(sales_series: dict, year_now: str, n: int) -> Tuple[Optional[float], Optional[str]]:
    return _series_cagr(sales_series, year_now, n)


def pat_cagr(net_profit_series: dict, year_now: str, n: int) -> Tuple[Optional[float], Optional[str]]:
    return _series_cagr(net_profit_series, year_now, n)


def eps_cagr(eps_series: dict, year_now: str, n: int) -> Tuple[Optional[float], Optional[str]]:
    return _series_cagr(eps_series, year_now, n)
