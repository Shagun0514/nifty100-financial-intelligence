from typing import Optional
from fastapi import APIRouter, HTTPException
from src.api.db import get_conn
from src.screener.engine import build_universe, compute_composite_scores

router = APIRouter(prefix="/screener", tags=["screener"])


@router.get("")
def screener(min_roe: Optional[float] = None, max_de: Optional[float] = None,
             min_fcf: Optional[float] = None, sector: Optional[str] = None,
             min_rev_cagr_5yr: Optional[float] = None, min_pat_cagr_5yr: Optional[float] = None,
             max_pe: Optional[float] = None):
    """Ranked company list filtered by the given thresholds. 400 on invalid parameter values."""
    for name, val in [("min_roe", min_roe), ("max_de", max_de), ("min_fcf", min_fcf),
                       ("min_rev_cagr_5yr", min_rev_cagr_5yr), ("min_pat_cagr_5yr", min_pat_cagr_5yr),
                       ("max_pe", max_pe)]:
        if val is not None and val != val:  # NaN check
            raise HTTPException(status_code=400, detail=f"Invalid value for {name}")

    conn = get_conn()
    universe = build_universe(conn)
    conn.close()
    if universe.empty:
        return []

    universe["composite_score"] = compute_composite_scores(universe, sector_relative=False)
    df = universe

    if sector:
        df = df[df["broad_sector"] == sector]
    if min_roe is not None:
        df = df[df["return_on_equity_pct"].fillna(-1e9) >= min_roe]
    if max_de is not None:
        df = df[(df["broad_sector"] == "Financials") | (df["debt_to_equity"].fillna(1e9) <= max_de)]
    if min_fcf is not None:
        df = df[df["free_cash_flow_cr"].fillna(-1e9) >= min_fcf]
    if min_rev_cagr_5yr is not None:
        df = df[df["revenue_cagr_5yr"].fillna(-1e9) >= min_rev_cagr_5yr]
    if min_pat_cagr_5yr is not None:
        df = df[df["pat_cagr_5yr"].fillna(-1e9) >= min_pat_cagr_5yr]
    if max_pe is not None and "pe_ratio" in df.columns:
        df = df[df["pe_ratio"].fillna(1e9) <= max_pe]

    df = df.sort_values("composite_score", ascending=False)
    cols = ["company_id", "company_name", "broad_sector", "composite_score",
            "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
            "revenue_cagr_5yr", "pat_cagr_5yr"]
    cols = [c for c in cols if c in df.columns]
    records = df[cols].to_dict(orient="records")
    # NaN isn't valid JSON; convert to None before returning
    return [{k: (None if isinstance(v, float) and v != v else v) for k, v in row.items()} for row in records]
