import math
from src.analytics.cagr import compute_cagr, revenue_cagr, TURNAROUND, DECLINE_TO_LOSS, \
    BOTH_NEGATIVE, ZERO_BASE, INSUFFICIENT


def test_cagr_normal():
    val, flag = compute_cagr(100, 161.05, 5)
    assert flag is None and math.isclose(val, 10.0, abs_tol=0.1)


def test_cagr_turnaround():
    val, flag = compute_cagr(-100, 200, 3)
    assert val is None and flag == TURNAROUND


def test_cagr_decline_to_loss():
    val, flag = compute_cagr(100, -50, 3)
    assert val is None and flag == DECLINE_TO_LOSS


def test_cagr_both_negative():
    val, flag = compute_cagr(-100, -50, 3)
    assert val is None and flag == BOTH_NEGATIVE


def test_cagr_zero_base():
    val, flag = compute_cagr(0, 100, 3)
    assert val is None and flag == ZERO_BASE


def test_cagr_insufficient_years_param():
    val, flag = compute_cagr(100, 200, 5, years_available=3)
    assert val is None and flag == INSUFFICIENT


def test_cagr_insufficient_none_values():
    val, flag = compute_cagr(None, 200, 5)
    assert val is None and flag == INSUFFICIENT


def test_revenue_cagr_series_normal():
    series = {f"{y}-03": 100 * (1.1 ** i) for i, y in enumerate(range(2018, 2024))}
    val, flag = revenue_cagr(series, "2023-03", 5)
    assert flag is None and math.isclose(val, 10.0, abs_tol=0.5)


def test_revenue_cagr_series_insufficient_history():
    series = {"2022-03": 100, "2023-03": 110}
    val, flag = revenue_cagr(series, "2023-03", 5)
    assert val is None and flag == INSUFFICIENT


def test_revenue_cagr_series_turnaround():
    series = {"2018-03": -50, "2019-03": 10, "2020-03": 20, "2021-03": 30, "2022-03": 40, "2023-03": 60}
    val, flag = revenue_cagr(series, "2023-03", 5)
    assert val is None and flag == TURNAROUND
