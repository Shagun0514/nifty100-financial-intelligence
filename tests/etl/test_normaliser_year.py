import pytest
from src.etl.normaliser import normalize_year

CASES = [
    ("Mar-23", "2023-03"), ("Mar 23", "2023-03"), ("March-2023", "2023-03"),
    ("FY24", "2024-03"), ("fy24", "2024-03"), ("FY 2019", "2019-03"),
    ("Dec-22", "2022-12"), ("dec-2022", "2022-12"), ("Jun-23", "2023-06"),
    ("jun 23", "2023-06"), ("2023", "2023-03"), ("2023-03", "2023-03"),
    (2023, "2023-03"), (2023.0, "2023-03"), ("21", "2021-03"),
    ("99", "1999-03"), ("  FY22  ", "2022-03"), ("Sep-20", "2020-09"),
    ("Nov-2021", "2021-11"), ("Feb-19", "2019-02"),
]


@pytest.mark.parametrize("raw,expected", CASES)
def test_normalize_year_valid(raw, expected):
    assert normalize_year(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "nan", "xyz", "13/45/67"])
def test_normalize_year_invalid(raw):
    with pytest.raises(ValueError):
        normalize_year(raw)
