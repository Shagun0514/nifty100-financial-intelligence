import sqlite3
import os
import pytest
import pandas as pd
from src.analytics.clustering import _impute_sector_median, name_clusters, build_feature_matrix, FEATURES

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")


def test_impute_sector_median_fills_within_sector():
    df = pd.DataFrame({"broad_sector": ["IT", "IT", "IT"], "roe": [10.0, None, 30.0]})
    out = _impute_sector_median(df, ["roe"], "broad_sector")
    assert out["roe"].iloc[1] == 20.0


def test_impute_sector_median_global_fallback_if_sector_all_null():
    df = pd.DataFrame({"broad_sector": ["IT", "IT", "FMCG"], "roe": [None, None, 15.0]})
    out = _impute_sector_median(df, ["roe"], "broad_sector")
    assert out["roe"].iloc[0] == 15.0


def test_name_clusters_assigns_distinct_names():
    df = pd.DataFrame({
        "cluster_id": [0, 0, 1, 1],
        "return_on_equity_pct": [25, 25, 2, 2], "debt_to_equity": [0.3, 0.3, 3.0, 3.0],
        "revenue_cagr_5yr": [15, 15, -20, -20], "fcf_cagr_5yr": [10, 10, -20, -20],
        "operating_profit_margin_pct": [20, 20, 5, 5],
    })
    names = name_clusters(df)
    assert names[0] != names[1]


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "cluster_test.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    for cid in ["A", "B"]:
        conn.execute("INSERT INTO companies (id, company_name) VALUES (?,?)", (cid, cid))
        conn.execute("INSERT INTO sectors (company_id, broad_sector) VALUES (?, 'IT')", (cid,))
        conn.execute("""INSERT INTO financial_ratios
            (company_id, year, return_on_equity_pct, debt_to_equity, revenue_cagr_5yr, operating_profit_margin_pct)
            VALUES (?, '2024-03', 20, 0.5, 10, 15)""", (cid,))
        for y in [f"{yr}-03" for yr in range(2019, 2024)]:
            conn.execute("INSERT INTO cashflow (company_id, year, operating_activity, investing_activity) "
                        "VALUES (?,?,100,-20)", (cid, y))
    conn.commit()
    conn.close()
    return path


def test_build_feature_matrix_includes_fcf_cagr(db):
    conn = sqlite3.connect(db)
    df = build_feature_matrix(conn)
    assert "fcf_cagr_5yr" in df.columns
    assert len(df) == 2
    for f in FEATURES:
        assert df[f].notna().all()
    conn.close()
