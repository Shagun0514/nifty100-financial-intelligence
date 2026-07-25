from src.nlp.parser import parse_text


def test_parse_normal():
    assert parse_text("10 Years: 21%") == (10, 21.0)


def test_parse_no_colon():
    assert parse_text("5 Years 24%") == (5, 24.0)


def test_parse_extra_whitespace():
    assert parse_text("3 Years:       17%") == (3, 17.0)


def test_parse_decimal_value():
    assert parse_text("10 Years:     15.5%") == (10, 15.5)


def test_parse_singular_year():
    assert parse_text("1 Year: 8%") == (1, 8.0)


def test_parse_unmatched_returns_none():
    assert parse_text("not a valid growth string") is None


def test_parse_none_input():
    assert parse_text(None) is None


def test_parse_empty_string():
    assert parse_text("") is None
