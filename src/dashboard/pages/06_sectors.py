import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import get_sectors, get_ratios, get_companies, get_valuation

st.set_page_config(page_title="Sector Analysis | Nifty 100 Analytics", layout="wide")
st.title("Sector Analysis")

sectors = get_sectors()
if sectors.empty:
    st.warning("No sector data loaded.")
    st.stop()

sector_choice = st.selectbox("Sector", sorted(sectors["broad_sector"].dropna().unique()))

ratios = get_ratios()
companies = get_companies()
val = get_valuation()

conn = sqlite3.connect(os.getenv("DB_PATH", "nifty100.db"))
sales_df = pd.read_sql_query("SELECT company_id, year, sales FROM profitandloss", conn)
conn.close()
sales_latest = sales_df.sort_values("year").groupby("company_id").tail(1)[["company_id", "sales"]]

latest_ratios = ratios.sort_values("year").groupby("company_id").tail(1)
merged = latest_ratios.merge(companies, on="company_id", how="left").merge(sales_latest, on="company_id", how="left")
merged = merged[merged["broad_sector"] == sector_choice]

if not val.empty:
    val_latest = val.sort_values("year").groupby("company_id").tail(1)
    merged = merged.merge(val_latest[["company_id", "market_cap_crore"]], on="company_id", how="left")
else:
    merged["market_cap_crore"] = None

if merged.empty:
    st.info("No companies found for this sector.")
    st.stop()

st.subheader(f"{sector_choice} — Revenue vs ROE")
merged["market_cap_crore_safe"] = merged["market_cap_crore"].fillna(merged["market_cap_crore"].median() or 1000)
fig = px.scatter(merged, x="sales", y="return_on_equity_pct",
                  size="market_cap_crore_safe", color="sub_sector",
                  hover_name="company_name",
                  labels={"sales": "Revenue (Cr)", "return_on_equity_pct": "ROE (%)"})
fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig, width='stretch')
st.caption("Bubble size = market cap, colour = sub-sector. "
           "⚠️ Market cap and price data are SIMULATED, not real market data.")

st.divider()
st.subheader("Sector Median KPIs")
median_metrics = merged[["return_on_equity_pct", "return_on_capital_employed_pct",
                          "net_profit_margin_pct", "debt_to_equity"]].median(numeric_only=True)
bar_fig = px.bar(x=median_metrics.index, y=median_metrics.values,
                  labels={"x": "Metric", "y": "Median Value"})
st.plotly_chart(bar_fig, width='stretch')
