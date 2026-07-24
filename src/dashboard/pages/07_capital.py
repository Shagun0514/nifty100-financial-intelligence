import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import get_capital_allocation, get_companies

st.set_page_config(page_title="Capital Allocation | Nifty 100 Analytics", layout="wide")
st.title("Capital Allocation Map")

alloc = get_capital_allocation()
if alloc.empty:
    st.warning("No capital_allocation.csv found. Run `make ratios` first (Sprint 2's ratio engine writes it).")
    st.stop()

companies = get_companies()
latest = alloc.sort_values("year").groupby("company_id").tail(1)
latest = latest.merge(companies, on="company_id", how="left")

st.subheader("All 92 Companies by Capital Allocation Pattern")
counts = latest.groupby("pattern_label")["company_id"].count().reset_index()
counts.columns = ["Pattern", "Count"]

fig = px.treemap(latest, path=["pattern_label", "company_id"], values=None)
fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, width='stretch')

st.divider()
st.subheader("Browse by Pattern")
pattern_choice = st.selectbox("Pattern", sorted(latest["pattern_label"].dropna().unique()))
subset = latest[latest["pattern_label"] == pattern_choice]
st.dataframe(subset[["company_id", "company_name", "cfo_sign", "cfi_sign", "cff_sign"]]
             .rename(columns={"company_id": "Ticker", "company_name": "Company",
                              "cfo_sign": "CFO", "cfi_sign": "CFI", "cff_sign": "CFF"}),
             width='stretch', hide_index=True)
