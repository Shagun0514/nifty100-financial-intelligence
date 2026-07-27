from fastapi import APIRouter, HTTPException
from src.api.db import get_conn

router = APIRouter(prefix="/sectors", tags=["sectors"])


@router.get("")
def list_sectors():
    """All broad sectors with company count and median ROE/P/E/D-E."""
    conn = get_conn()
    sectors = [r["broad_sector"] for r in conn.execute(
        "SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL").fetchall()]
    results = []
    for sector in sectors:
        companies = [r["company_id"] for r in conn.execute(
            "SELECT company_id FROM sectors WHERE broad_sector = ?", (sector,)).fetchall()]
        if not companies:
            continue
        placeholders = ",".join("?" * len(companies))
        ratios = conn.execute(
            f"SELECT return_on_equity_pct, debt_to_equity FROM financial_ratios "
            f"WHERE company_id IN ({placeholders}) AND year = "
            f"(SELECT MAX(year) FROM financial_ratios f2 WHERE f2.company_id = financial_ratios.company_id)",
            companies).fetchall()
        mc = conn.execute(
            f"SELECT pe_ratio FROM market_cap WHERE company_id IN ({placeholders}) AND year = "
            f"(SELECT MAX(year) FROM market_cap m2 WHERE m2.company_id = market_cap.company_id)",
            companies).fetchall()
        roes = [r["return_on_equity_pct"] for r in ratios if r["return_on_equity_pct"] is not None]
        des = [r["debt_to_equity"] for r in ratios if r["debt_to_equity"] is not None]
        pes = [r["pe_ratio"] for r in mc if r["pe_ratio"] is not None]
        results.append({
            "sector": sector, "company_count": len(companies),
            "median_roe": round(sorted(roes)[len(roes) // 2], 2) if roes else None,
            "median_pe": round(sorted(pes)[len(pes) // 2], 2) if pes else None,
            "median_de": round(sorted(des)[len(des) // 2], 2) if des else None,
        })
    conn.close()
    return results


@router.get("/{sector}/companies")
def sector_companies(sector: str):
    """All companies in a sector with their latest-year KPIs. 404 if sector unknown."""
    conn = get_conn()
    exists = conn.execute("SELECT 1 FROM sectors WHERE broad_sector = ? LIMIT 1", (sector,)).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")
    rows = conn.execute("""
        SELECT c.id, c.company_name, f.* FROM companies c
        JOIN sectors s ON s.company_id = c.id
        LEFT JOIN financial_ratios f ON f.company_id = c.id
            AND f.year = (SELECT MAX(year) FROM financial_ratios f2 WHERE f2.company_id = c.id)
        WHERE s.broad_sector = ?
    """, (sector,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
