"""Shared, cached data-access layer for the dashboard — Sprint 4, Day 22.
Every DB query function is wrapped with @st.cache_data(ttl=600).
"""
import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "nifty100.db")


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=600)
def get_companies():
    conn = _conn()
    df = pd.read_sql_query(
        "SELECT c.id as company_id, c.company_name, c.about_company, s.broad_sector, s.sub_sector "
        "FROM companies c LEFT JOIN sectors s ON s.company_id=c.id", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    conn = _conn()
    q = "SELECT * FROM financial_ratios"
    conds, params = [], []
    if ticker:
        conds.append("company_id=?")
        params.append(ticker)
    if year:
        conds.append("year=?")
        params.append(year)
    if conds:
        q += " WHERE " + " AND ".join(conds)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id=? ORDER BY year", conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker):
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id=? ORDER BY year", conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker):
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id=? ORDER BY year", conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors():
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_groups():
    conn = _conn()
    df = pd.read_sql_query("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name", conn)
    conn.close()
    return df["peer_group_name"].tolist()


@st.cache_data(ttl=600)
def get_peers(group_name):
    conn = _conn()
    df = pd.read_sql_query(
        "SELECT pg.company_id, pg.is_benchmark, c.company_name "
        "FROM peer_groups pg LEFT JOIN companies c ON c.id=pg.company_id "
        "WHERE pg.peer_group_name=?", conn, params=(group_name,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name):
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM peer_percentiles WHERE peer_group_name=?", conn, params=(group_name,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker=None):
    conn = _conn()
    q = "SELECT company_id, year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct, market_cap_crore FROM market_cap"
    params = []
    if ticker:
        q += " WHERE company_id=?"
        params.append(ticker)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    conn = _conn()
    df = pd.read_sql_query("SELECT pros, cons FROM prosandcons WHERE company_id=?", conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker):
    conn = _conn()
    df = pd.read_sql_query('SELECT Year, Annual_Report FROM documents WHERE company_id=? ORDER BY Year DESC',
                            conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_capital_allocation():
    """Reads output/capital_allocation.csv (written by Sprint 2's ratio engine)."""
    path = "output/capital_allocation.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)
