import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import sqlite3

from src.screener.engine import build_universe, compute_composite_scores, load_config

st.set_page_config(page_title="Screener | Nifty 100 Analytics", layout="wide")
st.title("Investment Screener")

conn = sqlite3.connect(os.getenv("DB_PATH", "nifty100.db"))
universe = build_universe(conn)
conn.close()

if universe.empty:
    st.warning("No data available. Run `make load`, `make ratios` first.")
    st.stop()

universe["composite_score"] = compute_composite_scores(universe, sector_relative=False)
config = load_config()

PRESET_DEFAULTS = {
    "Quality": dict(roe_min=15, de_max=1.0, fcf_min=0, revenue_cagr_5yr_min=10),
    "Value": dict(pe_max=20, pb_max=3.0, de_max=2.0, dividend_yield_min=1),
    "Growth": dict(pat_cagr_5yr_min=20, revenue_cagr_5yr_min=15, de_max=2.0),
    "Dividend": dict(dividend_yield_min=2, dividend_payout_max=80, fcf_min=0),
    "Debt-Free": dict(de_max=0, roe_min=12, sales_min=5000),
    "Turnaround": dict(revenue_cagr_3yr_min=10, fcf_positive_latest=True, de_declining_yoy=True),
}

st.sidebar.subheader("Presets")
preset_cols = st.sidebar.columns(2)
if "slider_defaults" not in st.session_state:
    st.session_state.slider_defaults = dict(roe_min=0, de_max=10.0, fcf_min=-99999, revenue_cagr_5yr_min=-99,
                                             pat_cagr_5yr_min=-99, opm_min=0, pe_max=200.0, pb_max=200.0,
                                             dividend_yield_min=0, icr_min=0)

for i, (label, thresholds) in enumerate(PRESET_DEFAULTS.items()):
    if preset_cols[i % 2].button(label):
        st.session_state.slider_defaults.update({k: v for k, v in thresholds.items() if isinstance(v, (int, float))})

st.sidebar.subheader("Custom Filters")
d = st.session_state.slider_defaults
roe_min = st.sidebar.slider("ROE min (%)", 0, 60, int(d.get("roe_min", 0)))
de_max = st.sidebar.slider("D/E max", 0.0, 10.0, float(d.get("de_max", 10.0)))
fcf_min = st.sidebar.number_input("FCF min (Cr)", value=float(d.get("fcf_min", -99999)))
rev_cagr_min = st.sidebar.slider("Revenue CAGR 5yr min (%)", -50, 100, int(d.get("revenue_cagr_5yr_min", -50)))
pat_cagr_min = st.sidebar.slider("PAT CAGR 5yr min (%)", -50, 100, int(d.get("pat_cagr_5yr_min", -50)))
opm_min = st.sidebar.slider("OPM min (%)", -50, 100, int(d.get("opm_min", -50)))
pe_max = st.sidebar.number_input("P/E max", value=float(d.get("pe_max", 200.0)))
pb_max = st.sidebar.number_input("P/B max", value=float(d.get("pb_max", 200.0)))
div_yield_min = st.sidebar.slider("Dividend Yield min (%)", 0.0, 10.0, float(d.get("dividend_yield_min", 0.0)))
icr_min = st.sidebar.slider("ICR min", 0, 20, int(d.get("icr_min", 0)))

filtered = universe.copy()
filtered = filtered[filtered["return_on_equity_pct"].fillna(-999) >= roe_min]
filtered = filtered[(filtered["broad_sector"] == "Financials") | (filtered["debt_to_equity"].fillna(999) <= de_max)]
filtered = filtered[filtered["free_cash_flow_cr"].fillna(-1e9) >= fcf_min]
filtered = filtered[filtered["revenue_cagr_5yr"].fillna(-999) >= rev_cagr_min]
filtered = filtered[filtered["pat_cagr_5yr"].fillna(-999) >= pat_cagr_min]
filtered = filtered[filtered["operating_profit_margin_pct"].fillna(-999) >= opm_min]
if "pe_ratio" in filtered.columns:
    filtered = filtered[filtered["pe_ratio"].fillna(1e9) <= pe_max]
if "pb_ratio" in filtered.columns:
    filtered = filtered[filtered["pb_ratio"].fillna(1e9) <= pb_max]
if "dividend_yield_pct" in filtered.columns:
    filtered = filtered[filtered["dividend_yield_pct"].fillna(-1) >= div_yield_min]
filtered = filtered[filtered["interest_coverage"].isna() | (filtered["interest_coverage"] >= icr_min)]

filtered = filtered.sort_values("composite_score", ascending=False)

st.markdown(f"### {len(filtered)} companies match your filters")

display_cols = ["company_id", "company_name", "broad_sector", "composite_score",
                 "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
                 "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct"]
display_cols = [c for c in display_cols if c in filtered.columns]
st.dataframe(filtered[display_cols], width='stretch', hide_index=True)

csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", data=csv, file_name="screener_results.csv", mime="text/csv")
