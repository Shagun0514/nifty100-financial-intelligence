from typing import Optional
from fastapi import APIRouter, HTTPException
from src.api.db import get_conn

router = APIRouter(prefix="/market-cap", tags=["valuation"])


@router.get("/{ticker}")
def market_cap_history(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    """Historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield) for a company."""
    conn = get_conn()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    q = "SELECT year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct, market_cap_crore FROM market_cap WHERE company_id = ?"
    params = [ticker]
    if from_year:
        q += " AND year >= ?"
        params.append(from_year)
    if to_year:
        q += " AND year <= ?"
        params.append(to_year)
    q += " ORDER BY year"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows
