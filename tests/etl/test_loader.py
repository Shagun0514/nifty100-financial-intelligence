"""10 tests verifying the loader reads correct row counts and column names per file."""
import os
import sqlite3
import importlib
import pandas as pd
import pytest

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")


@pytest.fixture
def loaded_db(tmp_path, monkeypatch):
    """Builds tiny fixture Excel files matching the real 12-file structure, loads them,
    and returns the resulting db path."""
    raw_dir = tmp_path / "raw"
    supp_dir = tmp_path / "supporting"
    raw_dir.mkdir()
    supp_dir.mkdir()

    companies = pd.DataFrame({"id": ["TCS", "INFY"], "company_name": ["Tata Consultancy", "Infosys"],
                               "face_value": [1, 5]})
    with pd.ExcelWriter(raw_dir / "companies.xlsx") as w:
        pd.DataFrame([["meta"] * len(companies.columns)], columns=companies.columns).to_excel(
            w, index=False, header=False, startrow=0)
        companies.to_excel(w, index=False, startrow=1)

    pl = pd.DataFrame({"id": [1, 2], "company_id": ["TCS", "INFY"], "year": ["Mar-23", "Mar-23"],
                        "sales": [1000, 800], "net_profit": [150, 100]})
    with pd.ExcelWriter(raw_dir / "profitandloss.xlsx") as w:
        pd.DataFrame([["meta"] * len(pl.columns)], columns=pl.columns).to_excel(w, index=False, header=False)
        pl.to_excel(w, index=False, startrow=1)

    for fname in ["balancesheet.xlsx", "cashflow.xlsx", "analysis.xlsx", "documents.xlsx", "prosandcons.xlsx"]:
        empty = pd.DataFrame({"company_id": []})
        with pd.ExcelWriter(raw_dir / fname) as w:
            pd.DataFrame([["meta"]], columns=["company_id"]).to_excel(w, index=False, header=False)
            empty.to_excel(w, index=False, startrow=1)

    sectors = pd.DataFrame({"company_id": ["TCS", "INFY"], "broad_sector": ["IT", "IT"]})
    sectors.to_excel(supp_dir / "sectors.xlsx", index=False)
    for fname in ["stock_prices.xlsx", "market_cap.xlsx", "financial_ratios.xlsx"]:
        pd.DataFrame({"company_id": []}).to_excel(supp_dir / fname, index=False)
    pd.DataFrame({"peer_group_name": ["IT Services"], "company_id": ["TCS"], "is_benchmark": [True]}).to_excel(
        supp_dir / "peer_groups.xlsx", index=False)

    db_path = str(tmp_path / "loader_test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("RAW_DATA_DIR", str(raw_dir))
    monkeypatch.setenv("SUPP_DATA_DIR", str(supp_dir))

    from src.etl import loader as loader_module
    importlib.reload(loader_module)
    loader_module.run_load()
    return db_path


def test_companies_row_count(loaded_db):
    conn = sqlite3.connect(loaded_db)
    assert conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 2
    conn.close()


def test_companies_column_names(loaded_db):
    conn = sqlite3.connect(loaded_db)
    cols = [c[1] for c in conn.execute("PRAGMA table_info(companies)")]
    assert "company_name" in cols and "id" in cols
    conn.close()


def test_profitandloss_row_count(loaded_db):
    conn = sqlite3.connect(loaded_db)
    assert conn.execute("SELECT COUNT(*) FROM profitandloss").fetchone()[0] == 2
    conn.close()


def test_profitandloss_year_normalised(loaded_db):
    conn = sqlite3.connect(loaded_db)
    years = [r[0] for r in conn.execute("SELECT year FROM profitandloss").fetchall()]
    assert all(y == "2023-03" for y in years)
    conn.close()


def test_profitandloss_columns(loaded_db):
    conn = sqlite3.connect(loaded_db)
    cols = [c[1] for c in conn.execute("PRAGMA table_info(profitandloss)")]
    assert "sales" in cols and "net_profit" in cols
    conn.close()


def test_sectors_loaded(loaded_db):
    conn = sqlite3.connect(loaded_db)
    assert conn.execute("SELECT COUNT(*) FROM sectors").fetchone()[0] == 2
    conn.close()


def test_peer_groups_loaded_and_expanded(loaded_db):
    conn = sqlite3.connect(loaded_db)
    rows = conn.execute("SELECT company_id, is_benchmark FROM peer_groups").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "TCS"
    assert rows[0][1] == 1
    conn.close()


def test_no_fk_violations(loaded_db):
    conn = sqlite3.connect(loaded_db)
    conn.execute("PRAGMA foreign_keys = ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == []
    conn.close()


def test_load_audit_file_written(loaded_db):
    assert os.path.exists("output/load_audit.csv")


def test_companies_ticker_uppercased(loaded_db):
    conn = sqlite3.connect(loaded_db)
    ids = [r[0] for r in conn.execute("SELECT id FROM companies").fetchall()]
    assert all(i == i.upper() for i in ids)
    conn.close()
