"""Parses analysis.xlsx's free-text growth fields — Sprint 5, Day 29.
Pattern: '10 Years: 21%' -> period_years=10, value_pct=21.0
"""
import os
import re
import csv
import sqlite3
import pandas as pd

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%")

METRIC_TO_RATIO_COL = {
    "compounded_sales_growth": "revenue_cagr_5yr",
    "compounded_profit_growth": "pat_cagr_5yr",
    "stock_price_cagr": None,   # no equivalent computed column
    "roe": "return_on_equity_pct",
}

FIELDS = ["compounded_sales_growth", "compounded_profit_growth", "stock_price_cagr", "roe"]


def parse_text(text):
    """Returns (period_years, value_pct) or None if it doesn't match the expected pattern."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    m = PATTERN.search(str(text))
    if not m:
        return None
    return int(m.group(1)), float(m.group(2))


def run(db_path=None, out_path="output/analysis_parsed.csv", fail_path="output/parse_failures.csv"):
    conn = sqlite3.connect(db_path or DB_PATH)
    analysis = pd.read_sql_query("SELECT * FROM analysis", conn)

    parsed_rows, failures = [], []
    for _, row in analysis.iterrows():
        for field in FIELDS:
            raw = row.get(field)
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                continue
            result = parse_text(raw)
            if result is None:
                failures.append({"company_id": row["company_id"], "field": field, "raw_text": raw})
                continue
            period, value = result
            parsed_rows.append({"company_id": row["company_id"], "metric_type": field,
                                 "period_years": period, "value_pct": value})

    parsed_df = pd.DataFrame(parsed_rows, columns=["company_id", "metric_type", "period_years", "value_pct"])

    # cross-validate vs Ratio Engine computed values, flag divergence > 5%
    divergences = []
    if not parsed_df.empty:
        fr = pd.read_sql_query("SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr, return_on_equity_pct "
                                "FROM financial_ratios", conn)
        latest = fr.sort_values("year").groupby("company_id").tail(1)
        for _, prow in parsed_df.iterrows():
            ratio_col = METRIC_TO_RATIO_COL.get(prow["metric_type"])
            if not ratio_col:
                continue
            match = latest[latest["company_id"] == prow["company_id"]]
            if match.empty or pd.isna(match[ratio_col].iloc[0]):
                continue
            computed = match[ratio_col].iloc[0]
            if abs(computed - prow["value_pct"]) > 5:
                divergences.append({"company_id": prow["company_id"], "metric_type": prow["metric_type"],
                                    "parsed_value": prow["value_pct"], "computed_value": round(computed, 2),
                                    "divergence_pct": round(abs(computed - prow["value_pct"]), 2)})

    os.makedirs("output", exist_ok=True)
    parsed_df.to_csv(out_path, index=False)

    with open(fail_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_id", "field", "raw_text"])
        w.writeheader()
        w.writerows(failures)

    if divergences:
        pd.DataFrame(divergences).to_csv("output/cagr_cross_validation.csv", index=False)

    print(f"analysis_parsed.csv: {len(parsed_df)} rows. parse_failures.csv: {len(failures)} rows. "
          f"Divergences > 5%: {len(divergences)}")
    conn.close()
    return parsed_df


if __name__ == "__main__":
    run()
