import pytest
from src.etl.normaliser import normalize_ticker

CASES = [
    ("tcs", "TCS"), (" TCS ", "TCS"), ("tcs ", "TCS"), ("Infy", "INFY"),
    ("HDFCBANK", "HDFCBANK"), ("m&m", "M&M"), ("bajaj-auto", "BAJAJ-AUTO"),
    ("Reliance", "RELIANCE"), ("itc", "ITC"), ("sbin", "SBIN"),
    ("tatamotors", "TATAMOTORS"), ("wipro", "WIPRO"), ("ongc", "ONGC"),
    ("l&t", "L&T"), ("hclTech", "HCLTECH"),
]


@pytest.mark.parametrize("raw,expected", CASES)
def test_normalize_ticker_valid(raw, expected):
    assert normalize_ticker(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "A", "THISISWAYTOOLONGXX"])
def test_normalize_ticker_invalid(raw):
    with pytest.raises(ValueError):
        normalize_ticker(raw)
