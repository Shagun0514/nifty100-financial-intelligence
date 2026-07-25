from src.reports.portfolio_summary import _arrow


def test_arrow_up():
    assert _arrow(20, 15) == "↑"


def test_arrow_down():
    assert _arrow(10, 15) == "↓"


def test_arrow_flat_within_2pct():
    assert _arrow(10.1, 10) == "→"


def test_arrow_none_values():
    assert _arrow(None, 10) == "→"
    assert _arrow(10, None) == "→"


def test_arrow_zero_prev():
    assert _arrow(10, 0) == "→"
