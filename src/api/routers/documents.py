from fastapi import APIRouter, HTTPException
from src.api.db import get_conn

router = APIRouter(prefix="/companies", tags=["documents"])


@router.get("/{ticker}/documents")
def get_documents(ticker: str):
    """Annual report links for a company, each with an is_url_valid boolean (format check, not a live HTTP call)."""
    conn = get_conn()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    rows = conn.execute(
        'SELECT Year as year, Annual_Report as url FROM documents WHERE company_id = ? ORDER BY Year DESC',
        (ticker,)).fetchall()
    conn.close()
    return [{"year": r["year"], "url": r["url"],
             "is_url_valid": bool(r["url"]) and str(r["url"]).startswith("http")} for r in rows]
