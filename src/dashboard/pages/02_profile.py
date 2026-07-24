import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_pros_cons

st.set_page_config(page_title="Company Profile | Nifty 100 Analytics", layout="wide")
st.title("Company Profile")

companies = get_companies()
if companies.empty:
    st.warning("No company data loaded.")
    st.stop()

options = (companies["company_id"] + " — " + companies["company_name"].fillna("")).tolist()
search = st.selectbox("Search company (ticker or name)", options=[""] + sorted(options))

ticker = search.split(" — ")[0] if search else None

if not ticker:
    st.info("Start typing a ticker or company name above.")
    st.stop()

row = companies[companies["company_id"] == ticker]
if row.empty:
    st.error("Ticker not found — please try another")
    st.stop()

row = row.iloc[0]
ratios = get_ratios(ticker=ticker)
pl = get_pl(ticker)

if ratios.empty:
    st.warning(f"No financial data available for {ticker} yet.")
    st.stop()

st.subheader(f"{row['company_name']} ({ticker})")
st.caption(f"{row.get('broad_sector', 'N/A')} — {row.get('sub_sector', 'N/A')}")
if isinstance(row.get("about_company"), str):
    st.write(row["about_company"])

latest = ratios.sort_values("year").iloc[-1]

def _fmt(v, suffix=""):
    return "N/A" if v is None or (isinstance(v, float) and v != v) else f"{v:.1f}{suffix}"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("ROE", _fmt(latest.get("return_on_equity_pct"), "%"))
c2.metric("ROCE", _fmt(latest.get("return_on_capital_employed_pct"), "%"))
c3.metric("Net Profit Margin", _fmt(latest.get("net_profit_margin_pct"), "%"))
c4.metric("D/E", _fmt(latest.get("debt_to_equity")))
c5.metric("Revenue CAGR 5yr", _fmt(latest.get("revenue_cagr_5yr"), "%"))
c6.metric("FCF (Cr)", _fmt(latest.get("free_cash_flow_cr")))

st.divider()

if not pl.empty:
    left, right = st.columns(2)
    with left:
        st.subheader("Revenue & Net Profit (10yr)")
        recent = pl.tail(10)
        fig = go.Figure()
        fig.add_bar(x=recent["year"], y=recent["sales"], name="Revenue")
        fig.add_bar(x=recent["year"], y=recent["net_profit"], name="Net Profit")
        fig.update_layout(barmode="group", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width='stretch')

    with right:
        st.subheader("ROE & ROCE (10yr)")
        r_recent = ratios.sort_values("year").tail(10)
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=r_recent["year"], y=r_recent["return_on_equity_pct"], name="ROE"),
                        secondary_y=False)
        fig2.add_trace(go.Scatter(x=r_recent["year"], y=r_recent["return_on_capital_employed_pct"], name="ROCE"),
                        secondary_y=True)
        fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig2, width='stretch')
else:
    st.info("No P&L history available for this company.")

st.divider()
st.subheader("Pros & Cons")
pc = get_pros_cons(ticker)
if pc.empty:
    st.caption("No pros/cons data available for this company.")
else:
    pcol, ccol = st.columns(2)
    with pcol:
        for pro in pc["pros"].dropna():
            st.success(f"✅ {pro}")
    with ccol:
        for con in pc["cons"].dropna():
            st.error(f"❌ {con}")
