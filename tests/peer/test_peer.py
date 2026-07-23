import sqlite3
import os
import pytest
from src.analytics.peer import compute_peer_percentiles, write_peer_percentiles

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "peer_test.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    it_companies = [("TCS", 40.0, 0.1), ("INFY", 30.0, 0.2), ("HCLTECH", 20.0, 0.3)]
    for cid, roe, de in it_companies:
        conn.execute("INSERT INTO companies (id, company_name) VALUES (?,?)", (cid, cid))
        conn.execute("INSERT INTO sectors (company_id, broad_sector) VALUES (?, 'Information Technology')", (cid,))
        conn.execute("INSERT INTO peer_groups (peer_group_name, company_id, is_benchmark) VALUES ('IT Services', ?, ?)",
                     (cid, 1 if cid == "TCS" else 0))
        conn.execute("""INSERT INTO financial_ratios (company_id, year, return_on_equity_pct, debt_to_equity)
                        VALUES (?, '2024-03', ?, ?)""", (cid, roe, de))
    conn.commit()
    conn.close()
    return path


def test_highest_roe_gets_highest_percentile(db):
    conn = sqlite3.connect(db)
    df = compute_peer_percentiles(conn)
    roe_rows = df[df["metric"] == "return_on_equity_pct"].sort_values("percentile_rank")
    top = roe_rows.iloc[-1]
    assert top["company_id"] == "TCS"  # TCS has ROE=40, the highest
    assert top["percentile_rank"] == 1.0
    conn.close()


def test_debt_to_equity_inverted(db):
    conn = sqlite3.connect(db)
    df = compute_peer_percentiles(conn)
    de_rows = df[df["metric"] == "debt_to_equity"].sort_values("percentile_rank")
    top = de_rows.iloc[-1]
    # TCS has lowest D/E (0.1) -> should rank highest after inversion
    assert top["company_id"] == "TCS"
    conn.close()


def test_write_peer_percentiles_roundtrip(db):
    conn = sqlite3.connect(db)
    df = compute_peer_percentiles(conn)
    write_peer_percentiles(conn, df)
    count = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    assert count == len(df)
    conn.close()


def test_ungrouped_company_handled_gracefully(tmp_path, capsys):
    path = str(tmp_path / "ungrouped.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.execute("INSERT INTO companies (id, company_name) VALUES ('LONER','Loner Ltd')")
    conn.execute("INSERT INTO financial_ratios (company_id, year, return_on_equity_pct) VALUES ('LONER','2024-03', 10)")
    conn.commit()
    df = compute_peer_percentiles(conn)
    captured = capsys.readouterr()
    assert "No peer group" in captured.out or df.empty
    conn.close()
