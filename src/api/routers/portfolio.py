import os
import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/stats")
def portfolio_stats():
    """P10-P90 percentile table for 10 core KPIs across all companies.
    Reads output/portfolio_stats.csv (written by src/analytics/portfolio_stats.py)."""
    path = "output/portfolio_stats.csv"
    if not os.path.exists(path):
        return {"message": "portfolio_stats.csv not found — run `make portfolio-stats` first", "data": []}
    df = pd.read_csv(path)
    records = df.to_dict(orient="records")
    return [{k: (None if isinstance(v, float) and v != v else v) for k, v in row.items()} for row in records]
