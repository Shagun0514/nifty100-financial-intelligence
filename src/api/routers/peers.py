from fastapi import APIRouter, HTTPException
from src.api.db import get_conn

router = APIRouter(tags=["peers"])

RADAR_AXES = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
              "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "interest_coverage"]


@router.get("/peers/{group_name}")
def peer_group(group_name: str):
    """All companies in a peer group with percentile rank for each of 10 metrics. 404 if unknown group."""
    conn = get_conn()
    exists = conn.execute("SELECT 1 FROM peer_groups WHERE peer_group_name = ? LIMIT 1", (group_name,)).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")
    members = conn.execute(
        "SELECT company_id, is_benchmark FROM peer_groups WHERE peer_group_name = ?", (group_name,)).fetchall()
    result = []
    for m in members:
        pcts = conn.execute(
            "SELECT metric, value, percentile_rank FROM peer_percentiles "
            "WHERE company_id = ? AND peer_group_name = ?", (m["company_id"], group_name)).fetchall()
        result.append({"company_id": m["company_id"], "is_benchmark": bool(m["is_benchmark"]),
                       "metrics": {p["metric"]: {"value": p["value"], "percentile_rank": p["percentile_rank"]}
                                   for p in pcts}})
    conn.close()
    return result


@router.get("/companies/{ticker}/peers/compare")
def peers_compare(ticker: str):
    """Radar data: 8-axis metric values for the company, its peer group average, and the benchmark company."""
    conn = get_conn()
    comp = conn.execute("SELECT id FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    group_row = conn.execute("SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (ticker,)).fetchone()
    if not group_row:
        conn.close()
        return {"company_id": ticker, "peer_group": None, "message": "No peer group assigned"}

    group_name = group_row["peer_group_name"]
    latest = conn.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1", (ticker,)).fetchone()
    company_vals = {axis: (dict(latest).get(axis) if latest else None) for axis in RADAR_AXES}

    members = [r["company_id"] for r in conn.execute(
        "SELECT company_id FROM peer_groups WHERE peer_group_name = ?", (group_name,)).fetchall()]
    group_avgs = {}
    for axis in RADAR_AXES:
        placeholders = ",".join("?" * len(members))
        vals = [r[axis] for r in conn.execute(
            f"SELECT {axis} FROM financial_ratios WHERE company_id IN ({placeholders}) "
            f"AND year = (SELECT MAX(year) FROM financial_ratios f2 WHERE f2.company_id = financial_ratios.company_id)",
            members).fetchall() if r[axis] is not None]
        group_avgs[axis] = round(sum(vals) / len(vals), 2) if vals else None

    bench_row = conn.execute(
        "SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1", (group_name,)).fetchone()
    bench_vals = {}
    if bench_row:
        bench_latest = conn.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
            (bench_row["company_id"],)).fetchone()
        bench_vals = {axis: (dict(bench_latest).get(axis) if bench_latest else None) for axis in RADAR_AXES}

    conn.close()
    return {"company_id": ticker, "peer_group": group_name, "company": company_vals,
            "peer_group_average": group_avgs, "benchmark": bench_vals}
