"""Loads the 12 real source files into nifty100.db.

data/raw/         -> companies, profitandloss, balancesheet, cashflow, analysis,
                     documents, prosandcons (header=1)
data/supporting/  -> sectors, stock_prices, market_cap, financial_ratios,
                     peer_groups (header=0)
"""
import os
import sqlite3
import csv
import pandas as pd
from .normaliser import normalize_year, normalize_ticker

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
CORE_DIR = os.getenv("RAW_DATA_DIR", "data/raw")
SUPP_DIR = os.getenv("SUPP_DATA_DIR", "data/supporting")
SCHEMA_PATH = "db/schema.sql"

CORE_FILES = [
    ("companies.xlsx", CORE_DIR, "companies", 1, False),
    ("profitandloss.xlsx", CORE_DIR, "profitandloss", 1, True),
    ("balancesheet.xlsx", CORE_DIR, "balancesheet", 1, True),
    ("cashflow.xlsx", CORE_DIR, "cashflow", 1, True),
    ("analysis.xlsx", CORE_DIR, "analysis", 1, False),
    ("documents.xlsx", CORE_DIR, "documents", 1, False),
    ("prosandcons.xlsx", CORE_DIR, "prosandcons", 1, False),
]
SUPP_FILES = [
    ("sectors.xlsx", SUPP_DIR, "sectors", 0, False),
    ("stock_prices.xlsx", SUPP_DIR, "stock_prices", 0, False),
    ("market_cap.xlsx", SUPP_DIR, "market_cap", 0, False),
    ("financial_ratios.xlsx", SUPP_DIR, "financial_ratios", 0, False),
]

LOAD_ORDER = ["companies", "sectors", "profitandloss", "balancesheet", "cashflow",
              "analysis", "documents", "prosandcons", "stock_prices",
              "market_cap", "financial_ratios", "peer_groups"]

REJECTS = []  # collected across the whole run -> output/load_rejects.csv


def init_schema(conn):
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())


def _clean_row(row, has_year, reasons):
    if "company_id" in row and row["company_id"] is not None:
        try:
            row["company_id"] = normalize_ticker(row["company_id"])
        except ValueError as e:
            reasons.append(f"bad company_id {row['company_id']!r}: {e}")
            row["company_id"] = None
    if "id" in row and isinstance(row.get("id"), str):
        try:
            row["id"] = normalize_ticker(row["id"])
        except ValueError:
            pass
    if has_year and "year" in row and row["year"] is not None:
        try:
            row["year"] = normalize_year(row["year"])
        except ValueError as e:
            reasons.append(f"bad year {row['year']!r}: {e}")
            row["year"] = None
    return row


def _insert_df(conn, df, table, has_year, audit, fname):
    df = df.where(pd.notnull(df), None)
    rows_read = len(df)
    loaded, rejected = 0, 0
    table_cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})")]
    for idx, r in df.iterrows():
        reasons = []
        row = _clean_row(r.to_dict(), has_year, reasons)
        cols = [c for c in row.keys() if c in table_cols]
        needs_company_id = "company_id" in table_cols
        bad = (not cols) or (has_year and row.get("year") is None) or \
              (needs_company_id and row.get("company_id") is None)
        if bad:
            rejected += 1
            REJECTS.append({"table": table, "file": fname, "row_index": idx,
                             "reason": "; ".join(reasons) or "missing/invalid required field"})
            continue
        placeholders = ",".join("?" * len(cols))
        sql = f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        try:
            conn.execute(sql, [row[c] for c in cols])
            loaded += 1
        except sqlite3.Error as e:
            rejected += 1
            ctx = f" [company_id={row.get('company_id')!r} year={row.get('year')!r}]"
            REJECTS.append({"table": table, "file": fname, "row_index": idx, "reason": f"sqlite error: {e}{ctx}"})
    audit.append({"table": table, "file": fname, "rows_read": rows_read,
                   "rows_loaded": loaded, "rows_rejected": rejected, "error": ""})


def _load_peer_groups(conn, audit):
    """Handles TWO possible shapes:
    A) already row-per-company: columns include peer_group_name, company_id[, is_benchmark]
    B) spec-style: 'Peer Group' | 'Members' (comma list) | 'Benchmark'
    """
    fpath = os.path.join(SUPP_DIR, "peer_groups.xlsx")
    if not os.path.exists(fpath):
        audit.append({"table": "peer_groups", "file": fpath, "rows_read": 0,
                       "rows_loaded": 0, "rows_rejected": 0, "error": "FILE NOT FOUND"})
        return
    df = pd.read_excel(fpath)
    df = df.where(pd.notnull(df), None)
    cols_lower = {c.lower().strip(): c for c in df.columns}
    loaded, rejected = 0, 0

    if "peer_group_name" in cols_lower and "company_id" in cols_lower:
        grp_col = cols_lower["peer_group_name"]
        co_col = cols_lower["company_id"]
        bench_col = cols_lower.get("is_benchmark")
        for idx, r in df.iterrows():
            try:
                ticker = normalize_ticker(r[co_col])
            except ValueError as e:
                rejected += 1
                REJECTS.append({"table": "peer_groups", "file": fpath, "row_index": idx, "reason": str(e)})
                continue
            is_bench = 1 if bench_col and bool(r[bench_col]) else 0
            try:
                conn.execute(
                    "INSERT INTO peer_groups (peer_group_name, company_id, is_benchmark) VALUES (?,?,?)",
                    (str(r[grp_col]).strip(), ticker, is_bench))
                loaded += 1
            except sqlite3.Error as e:
                rejected += 1
                REJECTS.append({"table": "peer_groups", "file": fpath, "row_index": idx, "reason": f"sqlite error: {e}"})
    else:
        grp_col = cols_lower.get("peer group") or df.columns[0]
        mem_col = cols_lower.get("members") or df.columns[1]
        bench_col = cols_lower.get("benchmark")
        for idx, r in df.iterrows():
            group = str(r[grp_col]).strip()
            members = [m.strip() for m in str(r[mem_col]).split(",") if m.strip()]
            bench = str(r[bench_col]).strip() if bench_col else None
            for m in members:
                try:
                    ticker = normalize_ticker(m)
                except ValueError as e:
                    rejected += 1
                    REJECTS.append({"table": "peer_groups", "file": fpath, "row_index": idx, "reason": str(e)})
                    continue
                is_bench = 1 if bench and ticker == normalize_ticker(bench) else 0
                try:
                    conn.execute(
                        "INSERT INTO peer_groups (peer_group_name, company_id, is_benchmark) VALUES (?,?,?)",
                        (group, ticker, is_bench))
                    loaded += 1
                except sqlite3.Error as e:
                    rejected += 1
                    REJECTS.append({"table": "peer_groups", "file": fpath, "row_index": idx, "reason": f"sqlite error: {e}"})

    audit.append({"table": "peer_groups", "file": fpath, "rows_read": len(df),
                   "rows_loaded": loaded, "rows_rejected": rejected, "error": ""})


def run_load():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    init_schema(conn)

    audit = []
    REJECTS.clear()
    by_table = {}
    for fname, d, table, header, has_year in CORE_FILES + SUPP_FILES:
        by_table[table] = (fname, d, header, has_year)

    for table in LOAD_ORDER:
        if table == "peer_groups":
            _load_peer_groups(conn, audit)
            conn.commit()
            continue
        if table not in by_table:
            continue
        fname, d, header, has_year = by_table[table]
        fpath = os.path.join(d, fname)
        if not os.path.exists(fpath):
            audit.append({"table": table, "file": fpath, "rows_read": 0,
                           "rows_loaded": 0, "rows_rejected": 0, "error": "FILE NOT FOUND"})
            continue
        try:
            df = pd.read_excel(fpath, header=header)
        except Exception as e:
            audit.append({"table": table, "file": fpath, "rows_read": 0,
                           "rows_loaded": 0, "rows_rejected": 0, "error": str(e)})
            continue
        _insert_df(conn, df, table, has_year, audit, fpath)
        conn.commit()

    os.makedirs("output", exist_ok=True)
    with open("output/load_audit.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["table", "file", "rows_read", "rows_loaded", "rows_rejected", "error"])
        w.writeheader()
        w.writerows(audit)

    with open("output/load_rejects.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["table", "file", "row_index", "reason"])
        w.writeheader()
        w.writerows(REJECTS)

    fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"Load complete. FK violations: {len(fk_errors)}. Rejects logged to output/load_rejects.csv ({len(REJECTS)} rows).")
    conn.close()
    return audit


if __name__ == "__main__":
    run_load()
