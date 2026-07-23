"""Cash flow KPIs & 8-pattern capital allocation classifier — Sprint 2, Day 11."""
from typing import List, Optional, Tuple


def free_cash_flow(operating_activity: float, investing_activity: float) -> float:
    """FCF = CFO + CFI. Negative is allowed."""
    return (operating_activity or 0) + (investing_activity or 0)


def cfo_quality_score(cfo_list: List[float], pat_list: List[float]) -> Tuple[Optional[float], str]:
    """Average CFO/PAT ratio over up to 5 years.
    >1.0 High Quality, 0.5-1.0 Moderate, <0.5 Accrual Risk. None if PAT sums to 0."""
    pairs = [(c, p) for c, p in zip(cfo_list[-5:], pat_list[-5:]) if p]
    if not pairs:
        return None, "Unknown"
    ratios = [c / p for c, p in pairs]
    avg = sum(ratios) / len(ratios)
    if avg > 1.0:
        label = "High Quality"
    elif avg >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
    return avg, label


def capex_intensity(investing_activity: float, sales: float) -> Tuple[Optional[float], str]:
    """abs(CFI)/sales*100. <3% Asset Light, 3-8% Moderate, >8% Capital Intensive."""
    if not sales:
        return None, "Unknown"
    pct = abs(investing_activity or 0) / sales * 100
    if pct < 3:
        label = "Asset Light"
    elif pct <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return pct, label


def fcf_conversion_rate(fcf: float, operating_profit: float) -> Optional[float]:
    """FCF / operating_profit * 100. None if operating_profit == 0."""
    if not operating_profit:
        return None
    return fcf / operating_profit * 100


PATTERN_LABELS = {
    ("+", "-", "-"): "Reinvestor",
    ("+", "+", "-"): "Liquidating Assets",
    ("-", "+", "+"): "Distress Signal",
    ("-", "-", "+"): "Growth Funded by Debt",
    ("+", "+", "+"): "Cash Accumulator",
    ("-", "-", "-"): "Pre-Revenue",
    ("+", "-", "+"): "Mixed",
    ("-", "+", "-"): "Mixed",
}


def _sign(x: float) -> str:
    return "+" if (x or 0) >= 0 else "-"


def capital_allocation_pattern(cfo: float, cfi: float, cff: float,
                                cfo_over_pat: Optional[float] = None) -> str:
    """Classifies the (CFO, CFI, CFF) sign pattern into one of 8 labels.
    (+,-,-) splits into Reinvestor vs Shareholder Returns based on cfo_over_pat (>1.0 -> returns)."""
    key = (_sign(cfo), _sign(cfi), _sign(cff))
    if key == ("+", "-", "-") and cfo_over_pat is not None and cfo_over_pat > 1.0:
        return "Shareholder Returns"
    return PATTERN_LABELS.get(key, "Mixed")
