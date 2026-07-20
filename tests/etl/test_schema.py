import sqlite3
import os
import pytest

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")
EXPECTED_TABLES = {"companies", "profitandloss", "balancesheet", "cashflow",
                   "analysis", "documents", "prosandcons", "sectors",
                   "stock_prices", "market_cap", "financial_ratios", "peer_groups"}


def _fresh_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    return conn


def test_all_12_tables_created():
    conn = _fresh_conn()
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert EXPECTED_TABLES.issubset(tables)


def test_foreign_keys_enforced():
    conn = _fresh_conn()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO profitandloss (id, company_id, year, sales) VALUES (1,'ZZZ','2021-03',100)")
        conn.commit()


def test_company_pk_unique():
    conn = _fresh_conn()
    conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS','Tata Consultancy')")
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS','Duplicate')")
        conn.commit()


def test_profitandloss_year_pk_unique():
    conn = _fresh_conn()
    conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS','Tata Consultancy')")
    conn.execute("INSERT INTO profitandloss (id, company_id, year, sales) VALUES (1,'TCS','2021-03',100)")
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO profitandloss (id, company_id, year, sales) VALUES (2,'TCS','2021-03',200)")
        conn.commit()
