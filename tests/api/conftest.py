import os
import sqlite3
import pytest

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")


@pytest.fixture
def api_db(tmp_path, monkeypatch):
    """Builds a small but complete synthetic database and points DB_PATH at it
    for the duration of the test (both src.api.db and downstream modules read
    DB_PATH lazily via os.getenv at call time, so this works without a server restart)."""
    path = str(tmp_path / "api_test.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    companies = [("TCS", "Tata Consultancy", "Information Technology"),
                 ("INFY", "Infosys", "Information Technology"),
                 ("HDFCBANK", "HDFC Bank", "Financials")]
    for cid, name, sector in companies:
        conn.execute("INSERT INTO companies (id, company_name, roe_percentage, roce_percentage) VALUES (?,?,?,?)",
                     (cid, name, 20.0, 25.0))
        conn.execute("INSERT INTO sectors (company_id, broad_sector, sub_sector) VALUES (?,?,?)",
                     (cid, sector, sector + " Sub"))
        conn.execute("INSERT INTO documents (company_id, Year, Annual_Report) VALUES (?,2024,?)",
                     (cid, "https://example.com/report.pdf"))
        for i, y in enumerate([f"{yr}-03" for yr in range(2019, 2024)]):
            roe = 30.0 if cid == "TCS" else (20.0 if cid == "INFY" else 10.0)
            conn.execute("""INSERT INTO financial_ratios
                (company_id, year, return_on_equity_pct, debt_to_equity, free_cash_flow_cr,
                 revenue_cagr_5yr, pat_cagr_5yr, operating_profit_margin_pct)
                VALUES (?,?,?,?,?,?,?,?)""",
                (cid, y, roe, 0.5, 100.0, 12.0, 10.0, 20.0))
            conn.execute("INSERT INTO profitandloss (id, company_id, year, sales, net_profit) VALUES (?,?,?,?,?)",
                        (hash((cid, y)) % 1000000, cid, y, 1000 + i * 50, 100 + i * 5))
        conn.execute("INSERT INTO market_cap (company_id, year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct) "
                     "VALUES (?, 2024, 25.0, 4.0, 15.0, 1.5)", (cid,))

    conn.execute("INSERT INTO peer_groups (peer_group_name, company_id, is_benchmark) VALUES ('IT Services','TCS',1)")
    conn.execute("INSERT INTO peer_groups (peer_group_name, company_id, is_benchmark) VALUES ('IT Services','INFY',0)")
    conn.commit()
    conn.close()

    monkeypatch.setenv("DB_PATH", path)
    return path
