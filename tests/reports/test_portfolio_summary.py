from src.reports.portfolio_summary import _arrow


def test_arrow_up():
    symbol, _ = _arrow(20, 15)
    assert symbol == "UP"


def test_arrow_down():
    symbol, _ = _arrow(10, 15)
    assert symbol == "DOWN"


def test_arrow_flat_within_2pct():
    symbol, _ = _arrow(10.1, 10)
    assert symbol == "FLAT"


def test_arrow_none_values():
    assert _arrow(None, 10)[0] == "FLAT"
    assert _arrow(10, None)[0] == "FLAT"


def test_arrow_zero_prev():
    assert _arrow(10, 0)[0] == "FLAT"
