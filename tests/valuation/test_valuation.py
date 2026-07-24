import sqlite3
import os
import pytest
from src.analytics.valuation import fcf_yield_pct, classify_valuation, build_valuation_table

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")


def test_fcf_yield_normal():
    assert fcf_yield_pct(500, 10000) == 5.0


def test_fcf_yield_zero_marketcap_none():
    assert fcf_yield_pct(500, 0) is None


def test_fcf_yield_missing_fcf_none():
    assert fcf_yield_pct(None, 10000) is None


def test_classify_caution():
    assert classify_valuation(40, 20) == "Caution"  # 40 > 20*1.5


def test_classify_discount():
    assert classify_valuation(10, 20) == "Discount"  # 10 < 20*0.7


def test_classify_fair():
    assert classify_valuation(22, 20) == "Fair"


def test_classify_missing_data_fair():
    assert classify_valuation(None, 20) == "Fair"
    assert classify_valuation(20, None) == "Fair"


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "val_test.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    for cid, pe, sector in [("TCS", 30, "Information Technology"), ("INFY", 25, "Information Technology"),
                             ("ITC", 20, "Consumer Staples")]:
        conn.execute("INSERT INTO companies (id, company_name) VALUES (?,?)", (cid, cid))
        conn.execute("INSERT INTO sectors (company_id, broad_sector) VALUES (?,?)", (cid, sector))
        conn.execute("INSERT INTO market_cap (company_id, year, pe_ratio, pb_ratio, ev_ebitda, market_cap_crore) "
                     "VALUES (?, 2024, ?, 5, 15, 100000)", (cid, pe))
        conn.execute("INSERT INTO financial_ratios (company_id, year, free_cash_flow_cr) VALUES (?, '2024-03', 2000)", (cid,))
    conn.commit()
    conn.close()
    return path


def test_build_valuation_table_has_all_companies(db):
    conn = sqlite3.connect(db)
    df = build_valuation_table(conn)
    assert len(df) == 3
    assert set(df["company_id"]) == {"TCS", "INFY", "ITC"}
    conn.close()


def test_build_valuation_table_fcf_yield_computed(db):
    conn = sqlite3.connect(db)
    df = build_valuation_table(conn)
    # FCF=2000, market_cap=100000 -> yield = 2%
    assert all(abs(v - 2.0) < 0.01 for v in df["fcf_yield_pct"])
    conn.close()
