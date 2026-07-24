import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_companies, get_ratios, get_sectors

st.set_page_config(page_title="Home | Nifty 100 Analytics", layout="wide")
st.title("Portfolio Overview")

ratios = get_ratios()
if ratios.empty:
    st.warning("No data in financial_ratios yet. Run `make ratios` first.")
    st.stop()

years = sorted(ratios["year"].dropna().unique())
default_idx = len(years) - 1 if years else 0
selected_year = st.sidebar.selectbox("Year", years, index=default_idx)

year_df = ratios[ratios["year"] == selected_year]
companies = get_companies()
sectors = get_sectors()
merged = year_df.merge(companies, on="company_id", how="left")

col1, col2, col3, col4, col5, col6 = st.columns(6)


def _safe_mean(series):
    return round(series.dropna().mean(), 1) if series.notna().any() else "N/A"


def _safe_median(series):
    return round(series.dropna().median(), 1) if series.notna().any() else "N/A"


col1.metric("Average ROE", f"{_safe_mean(year_df['return_on_equity_pct'])}%")
col2.metric("Median D/E", _safe_median(year_df["debt_to_equity"]))
col3.metric("Total Companies", companies["company_id"].nunique())
col4.metric("Median Revenue CAGR 5yr", f"{_safe_median(year_df['revenue_cagr_5yr'])}%")
debt_free_count = int((year_df["debt_to_equity"] == 0).sum())
col5.metric("Debt-Free Companies", debt_free_count)

try:
    from src.dashboard.utils.db import get_valuation
    val = get_valuation()
    val_latest = val.sort_values("year").groupby("company_id").tail(1) if not val.empty else val
    col6.metric("Median P/E", _safe_median(val_latest["pe_ratio"]) if not val_latest.empty else "N/A")
except Exception:
    col6.metric("Median P/E", "N/A")

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("Sector Breakdown")
    if not sectors.empty:
        sector_counts = sectors.groupby("broad_sector")["company_id"].nunique().reset_index()
        sector_counts.columns = ["Sector", "Companies"]
        fig = px.pie(sector_counts, names="Sector", values="Companies", hole=0.5)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No sector data loaded.")

with right:
    st.subheader("Top 5 by Composite Quality Score")
    try:
        import sqlite3
        from src.screener.engine import build_universe, compute_composite_scores
        conn = sqlite3.connect(os.getenv("DB_PATH", "nifty100.db"))
        universe = build_universe(conn)
        conn.close()
        if not universe.empty:
            universe["composite_score"] = compute_composite_scores(universe, sector_relative=False)
            top5 = universe.sort_values("composite_score", ascending=False).head(5)
            st.dataframe(top5[["company_id", "company_name", "broad_sector", "composite_score"]]
                         .rename(columns={"company_id": "Ticker", "company_name": "Company",
                                          "broad_sector": "Sector", "composite_score": "Score"}),
                         width='stretch', hide_index=True)
        else:
            st.info("No data available yet.")
    except Exception as e:
        st.info(f"Composite score unavailable: {e}")
