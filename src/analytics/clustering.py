"""KMeans clustering — Sprint 6, Day 36-37. 5 financial archetypes across all companies."""
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
FEATURES = ["return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr",
            "fcf_cagr_5yr", "operating_profit_margin_pct"]
N_CLUSTERS = 5
RANDOM_STATE = 42

CLUSTER_NAME_RULES = [
    ("High-Quality Compounders", lambda m: m["return_on_equity_pct"] > 20 and m["debt_to_equity"] < 1
        and m["revenue_cagr_5yr"] > 10),
    ("Defensive Dividend Payers", lambda m: m["operating_profit_margin_pct"] > 15 and m["revenue_cagr_5yr"] < 10
        and m["debt_to_equity"] < 1),
    ("Distressed / Turnaround", lambda m: m["return_on_equity_pct"] < 5 or m["fcf_cagr_5yr"] < -10),
    ("Value Cyclicals", lambda m: m["debt_to_equity"] > 1.5 and m["operating_profit_margin_pct"] < 15),
    ("Emerging Growth", lambda m: m["revenue_cagr_5yr"] > 15),
]


def _impute_sector_median(df, features, sector_col="broad_sector"):
    out = df.copy()
    for col in features:
        out[col] = out.groupby(sector_col)[col].transform(lambda s: s.fillna(s.median()))
        out[col] = out[col].fillna(out[col].median())
    return out


def _compute_fcf_cagr_5yr(conn):
    """fcf_cagr_5yr isn't a stored financial_ratios column; compute it here from
    cashflow history, same logic as src/analytics/cashflow_intelligence.py."""
    from src.analytics.cagr import compute_cagr
    cf = pd.read_sql_query("SELECT company_id, year, operating_activity, investing_activity FROM cashflow "
                            "ORDER BY company_id, year", conn)
    results = {}
    for cid, hist in cf.groupby("company_id"):
        fcf = (hist["operating_activity"].fillna(0) + hist["investing_activity"].fillna(0)).tolist()
        if len(fcf) >= 5:
            val, _flag = compute_cagr(fcf[-5], fcf[-1], 5)
            results[cid] = val
        else:
            results[cid] = None
    return results


def build_feature_matrix(conn):
    fr = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    sec = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    latest = fr.sort_values("year").groupby("company_id").tail(1)
    df = latest.merge(sec, on="company_id", how="left")
    fcf_cagr_map = _compute_fcf_cagr_5yr(conn)
    df["fcf_cagr_5yr"] = df["company_id"].map(fcf_cagr_map)
    for f in FEATURES:
        if f not in df.columns:
            df[f] = np.nan
    df = _impute_sector_median(df, FEATURES)
    return df


def generate_elbow_plot(X_scaled, path="reports/elbow_plot.png", k_range=range(2, 11)):
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(list(k_range), inertias, marker="o")
    ax.axvline(x=N_CLUSTERS, color="red", linestyle="--", label=f"k={N_CLUSTERS}")
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel("Inertia")
    ax.set_title("Elbow Plot")
    ax.legend()
    fig.tight_layout()
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def name_clusters(df, cluster_col="cluster_id"):
    means = df.groupby(cluster_col)[FEATURES].mean()
    names = {}
    used = set()
    for cid, row in means.iterrows():
        assigned = None
        for name, cond in CLUSTER_NAME_RULES:
            if name in used:
                continue
            try:
                if cond(row):
                    assigned = name
                    break
            except Exception:
                continue
        names[cid] = assigned or f"Cluster {cid}"
        if assigned:
            used.add(assigned)
    return names


def run(db_path=None, out_path="output/cluster_labels.csv", elbow_path="reports/elbow_plot.png"):
    conn = sqlite3.connect(db_path or DB_PATH)
    df = build_feature_matrix(conn)
    conn.close()

    if df.empty or len(df) < N_CLUSTERS:
        print(f"Not enough companies ({len(df)}) to form {N_CLUSTERS} clusters.")
        return pd.DataFrame()

    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    generate_elbow_plot(X_scaled, elbow_path)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    df["cluster_id"] = km.fit_predict(X_scaled)
    df["distance_from_centroid"] = np.linalg.norm(X_scaled - km.cluster_centers_[df["cluster_id"]], axis=1)

    names = name_clusters(df)
    df["cluster_name"] = df["cluster_id"].map(names)

    os.makedirs("output", exist_ok=True)
    result = df[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]].round(
        {"distance_from_centroid": 3})
    result.to_csv(out_path, index=False)

    print(f"cluster_labels.csv: {len(result)} companies across {result['cluster_id'].nunique()} clusters.")
    for cid, name in sorted(names.items()):
        count = (df["cluster_id"] == cid).sum()
        print(f"  Cluster {cid} ({name}): {count} companies")
    return result


if __name__ == "__main__":
    run()
