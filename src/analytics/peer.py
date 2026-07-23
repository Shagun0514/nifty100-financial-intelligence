"""Peer percentile rankings — Sprint 3, Day 18.
Computes PERCENT_RANK for 10 metrics within each peer group and populates
the peer_percentiles table. D/E is inverted (lower D/E -> higher percentile).
"""
import os
import sqlite3
import pandas as pd

DB_PATH = os.getenv("DB_PATH", "nifty100.db")

METRICS = {
    "return_on_equity_pct": False,
    "return_on_capital_employed_pct": False,
    "net_profit_margin_pct": False,
    "debt_to_equity": True,          # inverted: lower is better
    "free_cash_flow_cr": False,
    "pat_cagr_5yr": False,
    "revenue_cagr_5yr": False,
    "eps_cagr_5yr": False,
    "interest_coverage": False,
    "asset_turnover": False,
}


def _percent_rank(series):
    """Matches SQL PERCENT_RANK: (rank-1)/(n-1) among non-null values. n<=1 -> 0.5 for the lone value."""
    valid_mask = series.notna()
    n = int(valid_mask.sum())
    result = pd.Series([None] * len(series), index=series.index, dtype=object)
    if n == 0:
        return result
    if n == 1:
        result[valid_mask] = 0.5
        return result
    ranks = series[valid_mask].rank(method="average")
    pct = (ranks - 1) / (n - 1)
    result[valid_mask] = pct
    return result


def compute_peer_percentiles(conn):
    fr = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    if fr.empty:
        return pd.DataFrame()
    latest = fr.sort_values("year").groupby("company_id").tail(1)

    pg = pd.read_sql_query("SELECT peer_group_name, company_id FROM peer_groups", conn)
    if pg.empty:
        print("No peer groups found in peer_groups table.")
        return pd.DataFrame()

    df = pg.merge(latest, on="company_id", how="left")

    rows = []
    for group_name, gdf in df.groupby("peer_group_name"):
        gdf = gdf.reset_index(drop=True)
        for metric, invert in METRICS.items():
            if metric not in gdf.columns:
                continue
            pct = _percent_rank(gdf[metric])
            if invert:
                pct = pct.apply(lambda v: None if v is None else 1 - v)
            for i, row in gdf.iterrows():
                rows.append({"company_id": row["company_id"], "peer_group_name": group_name,
                             "metric": metric, "value": row[metric], "percentile_rank": pct[i],
                             "year": row.get("year")})

    # companies with no peer group at all
    all_companies = set(latest["company_id"])
    grouped_companies = set(pg["company_id"])
    ungrouped = all_companies - grouped_companies
    for cid in ungrouped:
        print(f"{cid}: No peer group assigned")

    return pd.DataFrame(rows)


def write_peer_percentiles(conn, df):
    conn.execute("DELETE FROM peer_percentiles")
    if df.empty:
        conn.commit()
        return
    conn.executemany(
        "INSERT OR REPLACE INTO peer_percentiles (company_id, peer_group_name, metric, value, percentile_rank, year) "
        "VALUES (?,?,?,?,?,?)",
        df[["company_id", "peer_group_name", "metric", "value", "percentile_rank", "year"]].itertuples(index=False, name=None))
    conn.commit()


def run(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    df = compute_peer_percentiles(conn)
    write_peer_percentiles(conn, df)
    n_groups = df["peer_group_name"].nunique() if not df.empty else 0
    print(f"peer_percentiles populated: {len(df)} rows across {n_groups} peer groups.")
    conn.close()
    return df


if __name__ == "__main__":
    run()
