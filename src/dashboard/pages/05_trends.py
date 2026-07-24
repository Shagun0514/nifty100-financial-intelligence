import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis | Nifty 100 Analytics", layout="wide")
st.title("Trend Analysis")

companies = get_companies()
if companies.empty:
    st.warning("No company data loaded.")
    st.stop()

options = sorted((companies["company_id"] + " — " + companies["company_name"].fillna("")).tolist())
search = st.selectbox("Company", options=[""] + options)
ticker = search.split(" — ")[0] if search else None
if not ticker:
    st.info("Pick a company to see its trend.")
    st.stop()

METRIC_OPTIONS = {
    "ROE (%)": "return_on_equity_pct", "ROCE (%)": "return_on_capital_employed_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct", "D/E": "debt_to_equity",
    "Free Cash Flow (Cr)": "free_cash_flow_cr", "Revenue CAGR 5yr (%)": "revenue_cagr_5yr",
    "PAT CAGR 5yr (%)": "pat_cagr_5yr", "Interest Coverage": "interest_coverage",
}
selected_labels = st.multiselect("Metrics to overlay (max 3)", list(METRIC_OPTIONS.keys()),
                                  default=["ROE (%)"], max_selections=3)

ratios = get_ratios(ticker=ticker)
if ratios.empty:
    st.error("Ticker not found — please try another")
    st.stop()

ratios = ratios.sort_values("year").tail(10)

fig = go.Figure()
for label in selected_labels:
    col = METRIC_OPTIONS[label]
    if col not in ratios.columns:
        continue
    series = ratios[col]
    yoy = series.pct_change().mul(100).round(1)
    text = [f"{v:+.1f}%" if pd.notna(v) else "" for v in yoy]
    fig.add_trace(go.Scatter(x=ratios["year"], y=series, mode="lines+markers+text",
                              text=text, textposition="top center", name=label))

fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), xaxis_title="Year")
st.plotly_chart(fig, width='stretch')
st.caption("Labels show year-over-year % change for each point.")
