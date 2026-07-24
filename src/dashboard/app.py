"""Nifty 100 Analytics — Streamlit dashboard entry point.
Run with: streamlit run src/dashboard/app.py
"""
import sys
import os

# make `from src...` imports work regardless of Streamlit's working directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st

st.set_page_config(page_title="Nifty 100 Analytics", layout="wide", initial_sidebar_state="expanded")

st.sidebar.title("Nifty 100 Analytics")
st.sidebar.caption("Use the pages above to navigate between screens.")

st.title("Nifty 100 Financial Intelligence Platform")
st.markdown("""
Welcome. Use the sidebar to navigate:

- **Home** — portfolio-wide summary KPIs and sector breakdown
- **Profile** — deep dive into a single company
- **Screener** — filter all 92 companies against custom or preset thresholds
- **Peers** — compare a company against its peer group
- **Trends** — multi-metric historical trend charts
- **Sectors** — sector-level bubble chart and benchmarks
- **Capital** — capital allocation pattern treemap
- **Reports** — annual report links per company

If a page shows *"Ticker not found"* or *"N/A"*, that's expected for companies with
partial data coverage — not a bug.
""")

db_path = os.getenv("DB_PATH", "nifty100.db")
if not os.path.exists(db_path):
    st.error(f"Database not found at `{db_path}`. Run `make load` and `make ratios` first.")
