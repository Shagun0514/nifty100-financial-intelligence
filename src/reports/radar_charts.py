"""Radar charts — Sprint 3, Day 19. 8 axes per company: ROE, ROCE, NPM, D/E (inverted),
FCF score, PAT CAGR 5yr, Revenue CAGR 5yr, Composite Score. Peer group average overlaid
as a dashed outline. Companies with no peer group get a standalone chart vs the Nifty 100 average.
"""
import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.screener.engine import build_universe, compute_composite_scores, winsor_scale

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
OUT_DIR = "reports/radar_charts"

AXES = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
        "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_score"]
AXIS_LABELS = ["ROE", "ROCE", "NPM", "D/E (inv)", "FCF", "PAT CAGR 5yr", "Rev CAGR 5yr", "Composite"]


def _score_axes(df):
    scored = pd.DataFrame(index=df.index)
    for col in AXES:
        if col == "debt_to_equity":
            proxy = df[col].apply(lambda v: None if pd.isna(v) or v == float("inf") else -v)
            scored[col] = winsor_scale(proxy)
        elif col == "composite_score":
            scored[col] = df[col]
        else:
            scored[col] = winsor_scale(df[col])
    return scored


def _plot_radar(company_id, company_scores, avg_scores, avg_label, path):
    n = len(AXES)
    angles = [i / n * 2 * np.pi for i in range(n)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    vals = list(company_scores) + [company_scores[0]]
    ax.plot(angles, vals, linewidth=2, label=company_id)
    ax.fill(angles, vals, alpha=0.25)

    avg_vals = list(avg_scores) + [avg_scores[0]]
    ax.plot(angles, avg_vals, linewidth=2, linestyle="--", label=avg_label)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(AXIS_LABELS, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_title(company_id, fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def generate_radar_charts(db_path=None, out_dir=OUT_DIR):
    conn = sqlite3.connect(db_path or DB_PATH)
    universe = build_universe(conn)
    if universe.empty:
        print("No data to chart.")
        conn.close()
        return []
    universe["composite_score"] = compute_composite_scores(universe, sector_relative=False)
    scored = _score_axes(universe)
    scored["company_id"] = universe["company_id"].values

    pg = pd.read_sql_query("SELECT peer_group_name, company_id FROM peer_groups", conn)
    conn.close()

    os.makedirs(out_dir, exist_ok=True)
    nifty_avg = scored[AXES].mean()
    written = []

    for _, row in scored.iterrows():
        cid = row["company_id"]
        company_scores = row[AXES].values.astype(float)
        group_row = pg[pg["company_id"] == cid]
        if not group_row.empty:
            group_name = group_row["peer_group_name"].iloc[0]
            peer_ids = pg[pg["peer_group_name"] == group_name]["company_id"].tolist()
            peer_scores = scored[scored["company_id"].isin(peer_ids)][AXES].mean().values.astype(float)
            label = f"{group_name} avg"
        else:
            peer_scores = nifty_avg.values.astype(float)
            label = "Nifty 100 avg"

        path = os.path.join(out_dir, f"{cid}_radar.png")
        _plot_radar(cid, company_scores, peer_scores, label, path)
        written.append(path)

    print(f"Generated {len(written)} radar charts in {out_dir}/")
    return written


if __name__ == "__main__":
    generate_radar_charts()
