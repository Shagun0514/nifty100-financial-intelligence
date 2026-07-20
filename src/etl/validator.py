"""16 Data Quality rules — exact spec, Section 14 of project doc.
CRITICAL rules must be resolved before Day 05 (full load). WARNING/INFO logged only.
"""
import sqlite3
import csv
import os

CRITICAL, WARNING, INFO = "CRITICAL", "WARNING", "INFO"


def _q(conn, sql):
    return conn.execute(sql).fetchall()


def run_all_rules(db_path="nifty100.db"):
    conn = sqlite3.connect(db_path)
    failures = []

    def add(rule, sev, msg, rows):
        for r in rows:
            failures.append({"rule": rule, "severity": sev, "detail": str(r), "message": msg})

    # DQ-01 Company PK uniqueness
    rows = _q(conn, "SELECT id, COUNT(*) c FROM companies GROUP BY id HAVING c>1")
    add("DQ-01", CRITICAL, "duplicate company id", rows)

    # DQ-02 Annual PK uniqueness (P&L/BS/CF)
    for t in ("profitandloss", "balancesheet", "cashflow"):
        rows = _q(conn, f"SELECT company_id, year, COUNT(*) c FROM {t} GROUP BY company_id, year HAVING c>1")
        add("DQ-02", CRITICAL, f"duplicate (company_id,year) in {t}", rows)

    # DQ-03 FK integrity
    rows = _q(conn, "PRAGMA foreign_key_check")
    add("DQ-03", CRITICAL, "FK violation - orphan row", rows)

    # DQ-04 Balance sheet balance (<1%)
    rows = _q(conn, """SELECT company_id, year, total_assets, total_liabilities FROM balancesheet
                       WHERE total_assets IS NOT NULL AND total_assets != 0
                       AND ABS(total_assets-total_liabilities)/total_assets >= 0.01""")
    add("DQ-04", WARNING, "balance sheet mismatch >=1%", rows)

    # DQ-05 OPM cross-check
    rows = _q(conn, """SELECT company_id, year, sales, operating_profit, opm_percentage FROM profitandloss
                       WHERE sales IS NOT NULL AND sales!=0
                       AND ABS(opm_percentage - (operating_profit/sales*100)) >= 1.0""")
    add("DQ-05", WARNING, "OPM% inconsistent with operating_profit/sales", rows)

    # DQ-06 Positive sales
    rows = _q(conn, "SELECT company_id, year, sales FROM profitandloss WHERE sales IS NOT NULL AND sales<=0")
    add("DQ-06", WARNING, "non-positive sales", rows)

    # DQ-07 Year format after normalize_year(): must match YYYY-MM
    for t in ("profitandloss", "balancesheet", "cashflow"):
        rows = _q(conn, f"""SELECT company_id, year FROM {t}
                            WHERE year IS NULL OR year NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'""")
        add("DQ-07", CRITICAL, f"unparseable/invalid year format in {t}", rows)

    # DQ-08 Ticker format: 2-12 chars, upper/stripped
    rows = _q(conn, "SELECT id FROM companies WHERE length(id)<2 OR length(id)>12 OR id!=upper(trim(id))")
    add("DQ-08", CRITICAL, "ticker format invalid (length or case)", rows)

    # DQ-09 Net cash check (+-10 Cr tolerance)
    rows = _q(conn, """SELECT company_id, year FROM cashflow
                       WHERE ABS((operating_activity+investing_activity+financing_activity)-net_cash_flow) > 10""")
    add("DQ-09", WARNING, "net_cash_flow mismatch vs CFO+CFI+CFF (>10 Cr)", rows)

    # DQ-10 Non-negative fixed assets
    rows = _q(conn, "SELECT company_id, year, fixed_assets FROM balancesheet WHERE fixed_assets < 0")
    add("DQ-10", WARNING, "negative fixed_assets", rows)

    # DQ-11 Tax rate range 0-60%
    rows = _q(conn, "SELECT company_id, year, tax_percentage FROM profitandloss WHERE tax_percentage NOT BETWEEN 0 AND 60")
    add("DQ-11", WARNING, "tax_percentage outside 0-60%", rows)

    # DQ-12 Dividend payout cap <=200%
    rows = _q(conn, "SELECT company_id, year, dividend_payout FROM profitandloss WHERE dividend_payout > 200")
    add("DQ-12", WARNING, "dividend_payout > 200%", rows)

    # DQ-13 URL validity (documents) - format check only (live HEAD request is optional/offline-safe)
    rows = _q(conn, """SELECT id, Annual_Report FROM documents
                       WHERE Annual_Report IS NOT NULL AND Annual_Report NOT LIKE 'http%'""")
    add("DQ-13", WARNING, "malformed Annual_Report URL", rows)

    # DQ-14 EPS sign consistency
    rows = _q(conn, "SELECT company_id, year, eps, net_profit FROM profitandloss WHERE net_profit>0 AND eps<=0")
    add("DQ-14", WARNING, "EPS not positive despite positive net_profit", rows)

    # DQ-15 Strict BS balance (informational counter, post DQ-04)
    rows = _q(conn, "SELECT COUNT(*) c FROM balancesheet WHERE total_assets != total_liabilities")
    add("DQ-15", INFO, "count of BS rows where assets != liabilities exactly", rows)

    # DQ-16 Coverage check: >=5 years of P&L/BS/CF
    for t in ("profitandloss", "balancesheet", "cashflow"):
        rows = _q(conn, f"SELECT company_id, COUNT(DISTINCT year) yrs FROM {t} GROUP BY company_id HAVING yrs<5")
        add("DQ-16", WARNING, f"company has <5 years of {t} history", rows)

    conn.close()
    return failures


def write_report(failures, out_path="output/validation_failures.csv"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rule", "severity", "message", "detail"])
        w.writeheader()
        w.writerows(failures)
    return out_path


if __name__ == "__main__":
    fails = run_all_rules()
    path = write_report(fails)
    crit = sum(1 for x in fails if x["severity"] == CRITICAL)
    print(f"Wrote {len(fails)} failures ({crit} CRITICAL) to {path}")
