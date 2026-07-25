import pandas as pd
import sqlite3
import os
import pytest
from src.analytics.cashflow_intelligence import _distress_flag, _deleveraging_flag, build_cashflow_intelligence

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")


def test_distress_flag_true():
    assert _distress_flag(-100, 50) is True


def test_distress_flag_false_when_cfo_positive():
    assert _distress_flag(100, 50) is False


def test_distress_flag_false_when_cff_negative():
    assert _distress_flag(-100, -50) is False


def test_deleveraging_flag_true():
    series = pd.Series([500, 300])
    assert _deleveraging_flag(-50, series) is True


def test_deleveraging_flag_false_cff_positive():
    series = pd.Series([500, 300])
    assert _deleveraging_flag(50, series) is False


def test_deleveraging_flag_false_debt_rising():
    series = pd.Series([300, 500])
    assert _deleveraging_flag(-50, series) is False


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "cf_test.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS','Tata')")
    conn.execute("INSERT INTO sectors (company_id, broad_sector) VALUES ('TCS','Information Technology')")
    for i, y in enumerate([f"{yr}-03" for yr in range(2019, 2024)]):
        conn.execute("INSERT INTO profitandloss (id,company_id,year,sales,operating_profit,net_profit) VALUES (?,?,?,?,?,?)",
                     (i + 1, "TCS", y, 1000 + i * 100, 200 + i * 20, 150 + i * 10))
        conn.execute("INSERT INTO balancesheet (id,company_id,year,borrowings) VALUES (?,?,?,?)",
                     (i + 1, "TCS", y, 500 - i * 50))
        conn.execute("INSERT INTO cashflow (id,company_id,year,operating_activity,investing_activity,financing_activity,net_cash_flow) VALUES (?,?,?,?,?,?,?)",
                     (i + 1, "TCS", y, 150, -30, -80, 40))
    conn.commit()
    conn.close()
    return path


def test_build_cashflow_intelligence_produces_row(db):
    conn = sqlite3.connect(db)
    df = build_cashflow_intelligence(conn)
    assert len(df) == 1
    assert df.iloc[0]["company_id"] == "TCS"
    assert df.iloc[0]["deleveraging_flag"] == True  # borrowings declining + CFF negative
    conn.close()
