import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_peer_groups, get_peers, get_peer_percentiles

st.set_page_config(page_title="Peer Comparison | Nifty 100 Analytics", layout="wide")
st.title("Peer Comparison")

groups = get_peer_groups()
if not groups:
    st.warning("No peer groups found. Run `make peers` first.")
    st.stop()

group = st.selectbox("Peer Group", groups)
members = get_peers(group)
pctiles = get_peer_percentiles(group)

if members.empty:
    st.info("No members found for this peer group.")
    st.stop()

st.subheader(f"{group} — {len(members)} companies")

company_choice = st.selectbox("Company to chart", members["company_id"].tolist())

AXES = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
        "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "interest_coverage"]
AXIS_LABELS = ["ROE", "ROCE", "NPM", "D/E", "FCF", "PAT CAGR", "Rev CAGR", "ICR"]

if not pctiles.empty:
    def _axis_values(cid, metrics):
        vals = []
        for m in metrics:
            rec = pctiles[(pctiles["company_id"] == cid) & (pctiles["metric"] == m)]
            vals.append(round((rec["percentile_rank"].iloc[0] or 0) * 100, 1) if not rec.empty else 0)
        return vals

    company_vals = _axis_values(company_choice, AXES)
    group_avg = []
    for m in AXES:
        rec = pctiles[pctiles["metric"] == m]
        group_avg.append(round(rec["percentile_rank"].dropna().mean() * 100, 1) if not rec.empty else 0)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=company_vals + [company_vals[0]],
                                   theta=AXIS_LABELS + [AXIS_LABELS[0]],
                                   fill="toself", name=company_choice))
    fig.add_trace(go.Scatterpolar(r=group_avg + [group_avg[0]],
                                   theta=AXIS_LABELS + [AXIS_LABELS[0]],
                                   name=f"{group} avg", line=dict(dash="dash")))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
    st.plotly_chart(fig, width='stretch')
else:
    st.info("No percentile data yet for this group. Run `make peers` first.")

st.divider()
st.subheader("Side-by-side")

rows = []
for _, m in members.iterrows():
    row = {"Ticker": m["company_id"], "Company": m["company_name"], "Benchmark": bool(m["is_benchmark"])}
    for metric in AXES:
        rec = pctiles[(pctiles["company_id"] == m["company_id"]) & (pctiles["metric"] == metric)]
        row[metric] = round(rec["value"].iloc[0], 2) if not rec.empty and rec["value"].iloc[0] is not None else None
    rows.append(row)

table = pd.DataFrame(rows)


def _highlight_benchmark(row):
    return ["background-color: #FFD966" if row["Benchmark"] else "" for _ in row]


if not table.empty:
    st.dataframe(table.style.apply(_highlight_benchmark, axis=1), width='stretch', hide_index=True)
