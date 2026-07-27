"""Shared SQLite connection helper for the FastAPI server."""
import os
import sqlite3


def get_conn():
    db_path = os.getenv("DB_PATH", "nifty100.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


ALL_TABLES = ["companies", "profitandloss", "balancesheet", "cashflow", "analysis",
              "documents", "prosandcons", "sectors", "stock_prices", "market_cap",
              "financial_ratios", "peer_groups", "peer_percentiles"]


ALL_TABLES = ["companies", "profitandloss", "balancesheet", "cashflow", "analysis",
              "documents", "prosandcons", "sectors", "stock_prices", "market_cap",
              "financial_ratios", "peer_groups"]
