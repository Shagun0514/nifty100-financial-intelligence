import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from src.api.db import get_conn

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def list_companies(sector: Optional[str] = None, market_cap_category: Optional[str] = None,
                    search: Optional[str] = None):
    """List all companies with id, name, sector, and pre-computed ROE/ROCE. Supports sector/search filters."""
    conn = get_conn()
    q = ("SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, "
         "c.roe_percentage as roe_pct, c.roce_percentage as roce_pct, s.market_cap_category "
         "FROM companies c LEFT JOIN sectors s ON s.company_id = c.id WHERE 1=1")
    params = []
    if sector:
        q += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        q += " AND s.market_cap_category = ?"
        params.append(market_cap_category)
    if search:
        q += " AND (c.company_name LIKE ? OR c.id LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


@router.get("/{ticker}")
def get_company(ticker: str):
    """Full company profile: base fields + sector + latest year KPIs. 404 if not found."""
    conn = get_conn()
    comp = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    sector = conn.execute("SELECT * FROM sectors WHERE company_id = ?", (ticker,)).fetchone()
    latest_ratio = conn.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1", (ticker,)).fetchone()
    conn.close()
    result = dict(comp)
    if sector:
        result["sector"] = dict(sector)
    if latest_ratio:
        result["latest_ratios"] = dict(latest_ratio)
    return result


def _year_filtered(conn, table, ticker, from_year, to_year):
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    q = f"SELECT * FROM {table} WHERE company_id = ?"
    params = [ticker]
    if from_year:
        q += " AND year >= ?"
        params.append(from_year)
    if to_year:
        q += " AND year <= ?"
        params.append(to_year)
    q += " ORDER BY year"
    return [dict(r) for r in conn.execute(q, params).fetchall()]


@router.get("/{ticker}/pl")
def get_pl(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """P&L history, optionally filtered by from_year/to_year in YYYY-MM format."""
    conn = get_conn()
    try:
        return _year_filtered(conn, "profitandloss", ticker, from_year, to_year)
    finally:
        conn.close()


@router.get("/{ticker}/bs")
def get_bs(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Balance sheet history, optionally filtered by from_year/to_year."""
    conn = get_conn()
    try:
        return _year_filtered(conn, "balancesheet", ticker, from_year, to_year)
    finally:
        conn.close()


@router.get("/{ticker}/cashflow")
def get_cashflow(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Cash flow history, optionally filtered by from_year/to_year."""
    conn = get_conn()
    try:
        return _year_filtered(conn, "cashflow", ticker, from_year, to_year)
    finally:
        conn.close()


@router.get("/{ticker}/ratios")
def get_ratios(ticker: str, year: Optional[str] = None):
    """All computed KPIs per year. Optional single-year filter."""
    conn = get_conn()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    q = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]
    if year:
        q += " AND year = ?"
        params.append(year)
    q += " ORDER BY year"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


@router.get("/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    """Returns the pre-generated tearsheet PDF as a binary download."""
    path = f"reports/tearsheets/{ticker}_tearsheet.pdf"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"No tearsheet found for '{ticker}'")
    return FileResponse(path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf")
