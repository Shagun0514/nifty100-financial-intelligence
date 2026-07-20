"""normalize_year() and normalize_ticker() — per project spec section 23.

normalize_year: 'Mar-23' / 'FY24' / 'Dec-22' / 2023 -> 'YYYY-MM' string.
Raises ValueError on unparseable input (row is rejected, DQ-07).
"""
import re

MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def normalize_year(raw) -> str:
    if raw is None:
        raise ValueError("PARSE_ERROR: None")
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        y = int(raw)
        return f"{_expand_2digit(y) if y < 100 else y}-03"  # bare int -> assume March FY close
    s = str(raw).strip().lower()
    if s in ("", "nan", "none"):
        raise ValueError(f"PARSE_ERROR: {raw!r}")

    m = re.match(r"^(\d{4})-(\d{2})$", s)  # already normalised: 2023-03
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    if s == "ttm":
        raise ValueError("TTM (Trailing Twelve Months) is not an annual period - intentionally skipped, not a data error")

    s_fy = re.sub(r"^fy\s*", "", s)

    m = re.match(r"^([a-z]{3,9})[\s-]?(\d{2,4})$", s_fy)  # Mar-23, March-2023, Dec-22
    if m and m.group(1)[:3] in MONTHS:
        mm = MONTHS[m.group(1)[:3]]
        yr_raw = m.group(2)
        yr = int(yr_raw) if len(yr_raw) == 4 else _expand_2digit(int(yr_raw))
        return f"{yr}-{mm}"

    m = re.match(r"^\d{4}$", s_fy)  # bare year -> assume March close
    if m:
        return f"{s_fy}-03"
    m = re.match(r"^\d{2}$", s_fy)
    if m:
        return f"{_expand_2digit(int(s_fy))}-03"

    raise ValueError(f"PARSE_ERROR: {raw!r}")


def _expand_2digit(y: int) -> int:
    return 2000 + y if y < 50 else 1900 + y


def normalize_ticker(raw) -> str:
    """Strip whitespace, uppercase. Valid length 2-12 chars (DQ-08)."""
    if raw is None:
        raise ValueError("ticker is None")
    s = str(raw).strip().upper()
    if s in ("", "NAN", "NONE"):
        raise ValueError(f"empty ticker: {raw!r}")
    if not (2 <= len(s) <= 12):
        raise ValueError(f"ticker length out of range (2-12): {raw!r}")
    return s
