import sqlite3
import os
import pytest
from src.etl.validator import run_all_rules, CRITICAL

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")


def _new_db(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS','Tata Consultancy')")
    return conn


def test_clean_db_has_no_critical_failures(tmp_path):
    path = str(tmp_path / "clean.db")
    conn = _new_db(path)
    conn.execute("""INSERT INTO profitandloss
        (id,company_id,year,sales,operating_profit,opm_percentage,tax_percentage,
         profit_before_tax,eps,net_profit,dividend_payout)
        VALUES (1,'TCS','2023-03',1000,210,21,25,210,10,150,40)""")
    conn.commit()
    conn.close()
    fails = run_all_rules(path)
    assert [f for f in fails if f["severity"] == CRITICAL] == []


def test_bad_sales_flagged_dq06(tmp_path):
    path = str(tmp_path / "bad.db")
    conn = _new_db(path)
    conn.execute("INSERT INTO profitandloss (id,company_id,year,sales) VALUES (1,'TCS','2023-03',-5)")
    conn.commit()
    conn.close()
    fails = run_all_rules(path)
    assert any(f["rule"] == "DQ-06" for f in fails)


def test_bs_mismatch_flagged_dq04(tmp_path):
    path = str(tmp_path / "bs.db")
    conn = _new_db(path)
    conn.execute("INSERT INTO balancesheet (id,company_id,year,total_assets,total_liabilities) VALUES (1,'TCS','2023-03',1000,900)")
    conn.commit()
    conn.close()
    fails = run_all_rules(path)
    assert any(f["rule"] == "DQ-04" for f in fails)
