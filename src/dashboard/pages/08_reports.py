import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import streamlit as st
import requests

from src.dashboard.utils.db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports | Nifty 100 Analytics", layout="wide")
st.title("Annual Reports")

companies = get_companies()
if companies.empty:
    st.warning("No company data loaded.")
    st.stop()

options = sorted((companies["company_id"] + " — " + companies["company_name"].fillna("")).tolist())
search = st.selectbox("Company", options=[""] + options)
ticker = search.split(" — ")[0] if search else None
if not ticker:
    st.info("Pick a company to see its annual report links.")
    st.stop()

docs = get_documents(ticker)
if docs.empty:
    st.error("Ticker not found — please try another" if ticker not in companies["company_id"].values
              else "No annual reports found for this company.")
    st.stop()

st.subheader(f"Annual Reports — {ticker}")
st.caption("Click 'Check link' to verify a report URL is still live (not checked automatically for speed).")

for _, row in docs.iterrows():
    col1, col2, col3 = st.columns([1, 4, 1])
    col1.write(f"**{row['Year']}**")
    col2.markdown(f"[{row['Annual_Report']}]({row['Annual_Report']})" if row["Annual_Report"] else "N/A")
    if row["Annual_Report"] and col3.button("Check link", key=f"check_{row['Year']}"):
        try:
            resp = requests.head(row["Annual_Report"], timeout=5, allow_redirects=True)
            if resp.status_code == 200:
                st.success("Link is live (200 OK)")
            else:
                st.error(f"Report unavailable (status {resp.status_code})")
        except Exception:
            st.error("Report unavailable (could not connect)")
