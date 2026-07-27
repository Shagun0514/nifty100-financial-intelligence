"""Portfolio-level statistics — Sprint 6, Day 37.
Correlation heatmap, per-sector Z-score outlier detection, P10-P90 portfolio stats.
"""
import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = os.getenv("DB_PATH", "nifty100.db")

KPIS = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
        "debt_to_equity", "interest_coverage", "asset_turnover", "free_cash_flow_cr",
        "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr"]


def _latest_year_ratios(conn):
    fr = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    return fr.sort_values("year").groupby("company_id").tail(1)


def generate_correlation_heatmap(conn, path="reports/correlation_heatmap.png"):
    latest = _latest_year_ratios(conn)
    corr = latest[KPIS].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
                annot_kws={"size": 7}, cbar_kws={"shrink": 0.8})
    ax.set_title("KPI Correlation Matrix (latest year)")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(fontsize=8)
    fig.tight_layout()
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def detect_outliers(conn, out_path="output/outlier_report.csv", z_threshold=3):
    latest = _latest_year_ratios(conn)
    sec = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    df = latest.merge(sec, on="company_id", how="left")

    rows = []
    for metric in KPIS:
        if metric not in df.columns:
            continue
        for sector, group in df.groupby("broad_sector"):
            vals = group[metric]
            mean, std = vals.mean(), vals.std()
            if not std or pd.isna(std):
                continue
            flagged = group[abs((vals - mean) / std) > z_threshold]
            for _, row in flagged.iterrows():
                rows.append({"company_id": row["company_id"], "metric": metric, "value": row[metric],
                            "z_score": round((row[metric] - mean) / std, 2), "sector": sector,
                            "sector_mean": round(mean, 2), "sector_std": round(std, 2)})

    out_df = pd.DataFrame(rows, columns=["company_id", "metric", "value", "z_score",
                                          "sector", "sector_mean", "sector_std"])
    os.makedirs("output", exist_ok=True)
    out_df.to_csv(out_path, index=False)
    return out_df


def compute_portfolio_stats(conn, out_path="output/portfolio_stats.csv"):
    latest = _latest_year_ratios(conn)
    rows = []
    for metric in KPIS:
        if metric not in latest.columns:
            continue
        vals = latest[metric].dropna()
        if vals.empty:
            continue
        rows.append({
            "metric": metric, "P10": round(vals.quantile(0.10), 2), "P25": round(vals.quantile(0.25), 2),
            "P50": round(vals.quantile(0.50), 2), "P75": round(vals.quantile(0.75), 2),
            "P90": round(vals.quantile(0.90), 2), "Mean": round(vals.mean(), 2), "Std": round(vals.std(), 2),
        })
    out_df = pd.DataFrame(rows)
    os.makedirs("output", exist_ok=True)
    out_df.to_csv(out_path, index=False)
    return out_df


def run(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    heatmap_path = generate_correlation_heatmap(conn)
    outliers = detect_outliers(conn)
    stats = compute_portfolio_stats(conn)
    print(f"correlation_heatmap.png -> {heatmap_path}")
    print(f"outlier_report.csv: {len(outliers)} flagged metric-company pairs")
    print(f"portfolio_stats.csv: {len(stats)} metrics summarised")
    conn.close()
    return outliers, stats


if __name__ == "__main__":
    run()
