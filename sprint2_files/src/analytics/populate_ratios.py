"""Sprint 2, Day 12-13: runs the full ratio engine for all 92 companies x all years,
writes financial_ratios table, output/capital_allocation.csv, output/ratio_edge_cases.log.
"""
import os
import csv
import sqlite3
from collections import defaultdict

from .ratios import (net_profit_margin, operating_profit_margin, return_on_equity,
                      return_on_capital_employed, return_on_assets, debt_to_equity,
                      interest_coverage, asset_turnover)
from .cagr import revenue_cagr, pat_cagr, eps_cagr
from .cashflow_kpis import (free_cash_flow, cfo_quality_score, capex_intensity,
                             fcf_conversion_rate, capital_allocation_pattern)

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
FINANCIALS_SECTOR = "Financials"
EDGE_LOG_PATH = "output/ratio_edge_cases.log"
CAPITAL_ALLOC_PATH = "output/capital_allocation.csv"


def _winsorize_scale(values, v):
    """Scale v to 0-100 using P10/P90 winsorisation against the full `values` list."""
    vals = sorted(x for x in values if x is not None)
    if not vals:
        return 50.0
    p10 = vals[int(0.10 * (len(vals) - 1))]
    p90 = vals[int(0.90 * (len(vals) - 1))]
    if p90 == p10:
        return 50.0
    x = max(p10, min(p90, v if v is not None else p10))
    return (x - p10) / (p90 - p10) * 100


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    companies = {r["id"]: dict(r) for r in conn.execute(
        "SELECT c.id, c.roce_percentage, c.roe_percentage, s.broad_sector FROM companies c "
        "LEFT JOIN sectors s ON s.company_id=c.id")}

    pl = defaultdict(dict)
    for r in conn.execute("SELECT * FROM profitandloss"):
        pl[r["company_id"]][r["year"]] = dict(r)
    bs = defaultdict(dict)
    for r in conn.execute("SELECT * FROM balancesheet"):
        bs[r["company_id"]][r["year"]] = dict(r)
    cf = defaultdict(dict)
    for r in conn.execute("SELECT * FROM cashflow"):
        cf[r["company_id"]][r["year"]] = dict(r)

    rows_out = []          # for financial_ratios table
    capital_alloc_rows = []  # for capital_allocation.csv
    edge_cases = []          # for ratio_edge_cases.log

    for company_id, years in pl.items():
        sector = companies.get(company_id, {}).get("broad_sector")
        sales_series = {y: v.get("sales") for y, v in years.items()}
        net_profit_series = {y: v.get("net_profit") for y, v in years.items()}
        eps_series = {y: v.get("eps") for y, v in years.items()}
        cfo_hist, pat_hist = [], []
        years_sorted = sorted(years.keys())

        for year in years_sorted:
            p = years[year]
            b = bs.get(company_id, {}).get(year, {})
            c = cf.get(company_id, {}).get(year, {})

            npm = net_profit_margin(p.get("net_profit"), p.get("sales"))
            opm, opm_mismatch = operating_profit_margin(p.get("operating_profit"), p.get("sales"),
                                                          p.get("opm_percentage"))
            roe = return_on_equity(p.get("net_profit"), b.get("equity_capital"), b.get("reserves"))
            roce = return_on_capital_employed(p.get("operating_profit"), p.get("depreciation"),
                                               b.get("equity_capital"), b.get("reserves"), b.get("borrowings"),
                                               sector)
            roa = return_on_assets(p.get("net_profit"), b.get("total_assets"))
            de, high_lev = debt_to_equity(b.get("borrowings"), b.get("equity_capital"), b.get("reserves"), sector)
            icr, icr_label, icr_risk = interest_coverage(p.get("operating_profit"), p.get("other_income"),
                                                          p.get("interest"))
            at = asset_turnover(p.get("sales"), b.get("total_assets"))

            fcf = free_cash_flow(c.get("operating_activity"), c.get("investing_activity"))
            capex_pct, capex_label = capex_intensity(c.get("investing_activity"), p.get("sales"))
            fcf_conv = fcf_conversion_rate(fcf, p.get("operating_profit"))

            cfo_hist.append(c.get("operating_activity") or 0)
            pat_hist.append(p.get("net_profit") or 0)
            cfo_q, cfo_q_label = cfo_quality_score(cfo_hist, pat_hist)

            rev_cagr, rev_flag = revenue_cagr(sales_series, year, 5)
            pat_cagr_v, pat_flag = pat_cagr(net_profit_series, year, 5)
            eps_cagr_v, eps_flag = eps_cagr(eps_series, year, 5)

            face_value = 1  # fallback; companies.face_value used if available
            bv_ps = None
            equity_cap = b.get("equity_capital")
            if equity_cap:
                fv = companies.get(company_id, {}).get("face_value") or face_value
                shares = equity_cap / fv if fv else None
                if shares:
                    bv_ps = ((b.get("equity_capital") or 0) + (b.get("reserves") or 0)) / shares

            cfo_over_pat = (c.get("operating_activity") / p.get("net_profit")) if p.get("net_profit") else None
            pattern = capital_allocation_pattern(c.get("operating_activity"), c.get("investing_activity"),
                                                  c.get("financing_activity"), cfo_over_pat)
            capital_alloc_rows.append({
                "company_id": company_id, "year": year,
                "cfo_sign": "+" if (c.get("operating_activity") or 0) >= 0 else "-",
                "cfi_sign": "+" if (c.get("investing_activity") or 0) >= 0 else "-",
                "cff_sign": "+" if (c.get("financing_activity") or 0) >= 0 else "-",
                "pattern_label": pattern,
            })

            if opm_mismatch:
                edge_cases.append(f"{company_id} {year}: OPM mismatch (computed vs source > 1%) - formula discrepancy")
            if icr_risk:
                edge_cases.append(f"{company_id} {year}: ICR < 1.5 - interest coverage risk flag")
            if high_lev:
                edge_cases.append(f"{company_id} {year}: D/E > 5 (non-Financials) - high leverage flag")
            for name, flag in (("revenue", rev_flag), ("PAT", pat_flag), ("EPS", eps_flag)):
                if flag:
                    edge_cases.append(f"{company_id} {year}: {name} 5yr CAGR = {flag}")

            rows_out.append({
                "company_id": company_id, "year": year,
                "net_profit_margin_pct": npm, "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe, "debt_to_equity": de,
                "interest_coverage": icr, "icr_label": icr_label, "asset_turnover": at,
                "free_cash_flow_cr": fcf, "capex_cr": abs(c.get("investing_activity") or 0),
                "earnings_per_share": p.get("eps"), "book_value_per_share": bv_ps,
                "dividend_payout_ratio_pct": p.get("dividend_payout"),
                "total_debt_cr": b.get("borrowings"), "cash_from_operations_cr": c.get("operating_activity"),
                "return_on_capital_employed_pct": roce, "return_on_assets_pct": roa,
                "high_leverage_flag": int(high_lev), "revenue_cagr_5yr": rev_cagr,
                "revenue_cagr_5yr_flag": rev_flag, "pat_cagr_5yr": pat_cagr_v, "pat_cagr_5yr_flag": pat_flag,
                "eps_cagr_5yr": eps_cagr_v, "eps_cagr_5yr_flag": eps_flag,
                "cfo_quality_score": cfo_q, "cfo_quality_label": cfo_q_label,
                "capex_intensity_pct": capex_pct, "capex_intensity_label": capex_label,
                "fcf_conversion_rate_pct": fcf_conv,
            })

        # Sprint 1's financial_ratios rows (from the source file) provide roce_percentage/roe_percentage
        # via companies table for cross-check (Day 13)
        latest_year = years_sorted[-1] if years_sorted else None
        if latest_year:
            comp = companies.get(company_id, {})
            latest_roce = next((r["return_on_capital_employed_pct"] for r in rows_out
                                 if r["company_id"] == company_id and r["year"] == latest_year), None)
            latest_roe = next((r["return_on_equity_pct"] for r in rows_out
                                if r["company_id"] == company_id and r["year"] == latest_year), None)
            src_roce = comp.get("roce_percentage")
            src_roe = comp.get("roe_percentage")
            if latest_roce is not None and src_roce is not None and abs(latest_roce - src_roce) > 5:
                edge_cases.append(f"{company_id}: computed ROCE {latest_roce:.1f}% vs source "
                                   f"{src_roce}% differ by >5% - data source issue")
            if latest_roe is not None and src_roe is not None and abs(latest_roe - src_roe) > 5:
                edge_cases.append(f"{company_id}: computed ROE {latest_roe:.1f}% vs source "
                                   f"{src_roe}% differ by >5% (source values can be stale/mis-scaled) - version difference")

    # Composite quality score: 0.3 ROE + 0.25 FCF(as CAGR proxy) + 0.25 ROCE + 0.20 (inverse D/E)
    roe_vals = [r["return_on_equity_pct"] for r in rows_out]
    roce_vals = [r["return_on_capital_employed_pct"] for r in rows_out]
    fcf_vals = [r["free_cash_flow_cr"] for r in rows_out]
    de_vals = [-r["debt_to_equity"] if r["debt_to_equity"] not in (None, float("inf")) else None for r in rows_out]
    for r in rows_out:
        s_roe = _winsorize_scale(roe_vals, r["return_on_equity_pct"])
        s_roce = _winsorize_scale(roce_vals, r["return_on_capital_employed_pct"])
        s_fcf = _winsorize_scale(fcf_vals, r["free_cash_flow_cr"])
        de_val = -r["debt_to_equity"] if r["debt_to_equity"] not in (None, float("inf")) else None
        s_de = _winsorize_scale(de_vals, de_val)
        r["composite_quality_score"] = round(0.30 * s_roe + 0.25 * s_fcf + 0.25 * s_roce + 0.20 * s_de, 1)

    # write to financial_ratios table
    cols = list(rows_out[0].keys()) if rows_out else []
    placeholders = ",".join("?" * len(cols))
    for r in rows_out:
        conn.execute(f"INSERT OR REPLACE INTO financial_ratios ({','.join(cols)}) VALUES ({placeholders})",
                     [r[c] for c in cols])
    conn.commit()

    os.makedirs("output", exist_ok=True)
    with open(CAPITAL_ALLOC_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"])
        w.writeheader()
        w.writerows(capital_alloc_rows)

    with open(EDGE_LOG_PATH, "w") as f:
        f.write(f"Ratio Engine edge case log - {len(edge_cases)} entries\n")
        f.write("=" * 60 + "\n")
        for line in edge_cases:
            f.write(line + "\n")

    count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    print(f"financial_ratios populated: {count} rows. "
          f"capital_allocation.csv: {len(capital_alloc_rows)} rows. "
          f"ratio_edge_cases.log: {len(edge_cases)} entries.")
    conn.close()


if __name__ == "__main__":
    run()
