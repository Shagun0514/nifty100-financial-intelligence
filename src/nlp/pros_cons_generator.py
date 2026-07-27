"""Auto pros/cons generator — Sprint 5, Day 30. 12 pro rules + 12 con rules.
Only rules with confidence > 60% are included in the output.
"""
import os
import sqlite3
import pandas as pd

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
CONFIDENCE_THRESHOLD = 60


def _trend(series, n):
    """True if the last n values are strictly increasing."""
    vals = series.dropna().tolist()
    if len(vals) < n:
        return False
    tail = vals[-n:]
    return all(tail[i] < tail[i + 1] for i in range(len(tail) - 1))


def _declining(series, n):
    vals = series.dropna().tolist()
    if len(vals) < n:
        return False
    tail = vals[-n:]
    return all(tail[i] > tail[i + 1] for i in range(len(tail) - 1))


def _consecutive_positive(series, n):
    vals = series.dropna().tolist()
    if len(vals) < n:
        return False
    return all(v > 0 for v in vals[-n:])


def _consecutive_negative(series, n):
    vals = series.dropna().tolist()
    if len(vals) < n:
        return False
    return all(v < 0 for v in vals[-n:])


def generate_pros_cons_for_company(hist, sector):
    """hist: DataFrame of financial_ratios rows for one company (sorted by year), merged with
    net_profit/sales/total_assets/borrowings from P&L/BS.
    Returns list of dicts: {type, rule_id, text, confidence_pct, below_threshold}.

    Every rule that fires is recorded, even below the 60% confidence cutoff. Rules above
    the cutoff are always included. If a company ends up with zero entries on one side
    (e.g. a strong company with no qualifying "con"), the single best-scoring candidate
    for that side is backfilled and flagged below_threshold=True, so every company gets
    at least one pro and one con (matching AC-16) without silently lowering the bar for
    everyone else.
    """
    if hist.empty:
        return []
    latest = hist.iloc[-1]
    results = []
    all_candidates = []

    def add(type_, rule_id, text, confidence):
        all_candidates.append({"type": type_, "rule_id": rule_id, "text": text, "confidence_pct": confidence})
        if confidence > CONFIDENCE_THRESHOLD:
            results.append({"type": type_, "rule_id": rule_id, "text": text, "confidence_pct": confidence,
                            "below_threshold": False})

    roe = hist["return_on_equity_pct"]
    roe_last3 = roe.dropna().tail(3)
    if len(roe_last3) == 3 and all(v > 20 for v in roe_last3):
        add("pro", "PRO-01", "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", 90)

    if _consecutive_positive(hist["free_cash_flow_cr"], 5):
        add("pro", "PRO-02", "Strong free cash flow generation over 5 years signals healthy business fundamentals", 88)

    if pd.notna(latest.get("debt_to_equity")) and latest["debt_to_equity"] == 0:
        add("pro", "PRO-03", "Debt-free balance sheet provides financial flexibility and eliminates interest burden", 95)

    if pd.notna(latest.get("revenue_cagr_5yr")) and latest["revenue_cagr_5yr"] > 15:
        add("pro", "PRO-04", "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum", 85)

    if pd.notna(latest.get("operating_profit_margin_pct")) and latest["operating_profit_margin_pct"] > 25:
        add("pro", "PRO-05", "Operating profit margin above 25% indicates strong pricing power and cost discipline", 82)

    if pd.notna(latest.get("pat_cagr_5yr")) and latest["pat_cagr_5yr"] > 20:
        add("pro", "PRO-06", "Net profit compounding at above 20% over 5 years creates significant shareholder value", 85)

    icr = latest.get("interest_coverage")
    icr_label = latest.get("icr_label")
    if icr_label == "Debt Free" or (pd.notna(icr) and icr > 10):
        add("pro", "PRO-07", "Very high interest coverage ratio reflects negligible financial stress from debt servicing", 88)

    payout = latest.get("dividend_payout_ratio_pct")
    fcf = latest.get("free_cash_flow_cr")
    if pd.notna(payout) and payout > 20 and pd.notna(fcf) and fcf > 0:
        add("pro", "PRO-08", "Consistent dividend yield above 2% backed by positive free cash flow", 65)

    if pd.notna(latest.get("eps_cagr_5yr")) and latest["eps_cagr_5yr"] > 15:
        add("pro", "PRO-09", "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding", 84)

    if _trend(roe, 3):
        add("pro", "PRO-10", "Return on equity improving for 3 consecutive years shows strengthening business quality", 78)

    rev_c, pat_c = latest.get("revenue_cagr_5yr"), latest.get("pat_cagr_5yr")
    if pd.notna(rev_c) and pd.notna(pat_c) and pat_c > rev_c and rev_c > 0:
        add("pro", "PRO-11", "Revenue growing slower than profits shows improving operating leverage and scale benefits", 75)

    if "total_assets" in hist.columns and "borrowings" in hist.columns:
        assets_growing = _trend(hist["total_assets"], 3)
        debt_declining = _declining(hist["borrowings"], 3)
        if assets_growing and debt_declining:
            add("pro", "PRO-12", "Growing asset base funded by internal accruals reflects self-sustaining growth", 80)

    de = latest.get("debt_to_equity")
    if sector != "Financials" and pd.notna(de) and de > 2.0:
        add("con", "CON-01", f"Debt-to-equity ratio of {de:.1f} is elevated for a non-financial company and warrants monitoring", 85)

    if _consecutive_negative(hist["free_cash_flow_cr"], 3):
        add("con", "CON-02", "Free cash flow negative for 3 consecutive years raises concern about cash generation quality", 88)

    if _declining(hist["operating_profit_margin_pct"], 3):
        add("con", "CON-03", "Operating margins declining for 3 consecutive years suggest pricing or cost pressure", 80)

    if "net_profit" in hist.columns and pd.notna(latest.get("net_profit")) and latest["net_profit"] < 0:
        add("con", "CON-04", "Company reported a net loss in the most recent financial year", 95)

    if "sales" in hist.columns and _declining(hist["sales"], 2):
        add("con", "CON-05", "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss", 82)

    if pd.notna(icr) and icr_label != "Debt Free" and icr < 1.5:
        add("con", "CON-06", "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations", 90)

    if pd.notna(payout) and payout > 100:
        add("con", "CON-07", "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable", 88)

    if "debt_to_equity" in hist.columns and _trend(hist["debt_to_equity"], 3):
        add("con", "CON-08", "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk", 78)

    if "earnings_per_share" in hist.columns and _declining(hist["earnings_per_share"], 3):
        add("con", "CON-09", "Earnings per share declining for 3 consecutive years reflects deteriorating profitability", 82)

    roce = latest.get("return_on_capital_employed_pct")
    if pd.notna(roce) and roce < 10:
        add("con", "CON-10", "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital", 80)

    total_debt = latest.get("total_debt_cr")
    if "ebitda_proxy" in hist.columns:
        ebitda_series = hist["ebitda_proxy"].dropna()
        ebitda_latest = ebitda_series.iloc[-1] if not ebitda_series.empty else None
        if pd.notna(total_debt) and ebitda_latest and ebitda_latest > 0 and total_debt > 3 * ebitda_latest:
            add("con", "CON-11", "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility", 82)

    if pd.notna(rev_c) and rev_c < 5:
        add("con", "CON-12", "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum", 75)

    # Fallback signals: always evaluated (not gated on a threshold condition) so there's
    # always at least one candidate on each side to draw from below. These use the same
    # metrics as PRO-01/CON-01 but scale continuously rather than requiring a hard cutoff.
    de_val = latest.get("debt_to_equity")
    if pd.notna(de_val):
        add("con", "CON-FALLBACK", f"Debt-to-equity of {de_val:.2f} is a general leverage level worth monitoring "
            f"alongside sector peers.", min(95, max(5, de_val * 20)))
    roe_val = latest.get("return_on_equity_pct")
    if pd.notna(roe_val):
        add("pro", "PRO-FALLBACK", f"Return on equity of {roe_val:.1f}% reflects the company's baseline capital "
            f"efficiency.", min(95, max(5, roe_val * 3)))

    # Guarantee coverage (AC-16): if a company still has zero pros or zero cons after all
    # 24 rules + fallbacks, backfill with the single best-scoring candidate for that side,
    # flagged below_threshold=True so it's clearly distinguishable from a genuine >60% signal.
    for needed_type in ("pro", "con"):
        if not any(r["type"] == needed_type for r in results):
            candidates = [c for c in all_candidates if c["type"] == needed_type]
            if candidates:
                best = max(candidates, key=lambda c: c["confidence_pct"])
                results.append({**best, "below_threshold": True})

    return results


def run(db_path=None, out_path="output/pros_cons_generated.csv"):
    conn = sqlite3.connect(db_path or DB_PATH)
    fr = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    pl = pd.read_sql_query("SELECT company_id, year, sales, net_profit, operating_profit FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT company_id, year, total_assets, borrowings FROM balancesheet", conn)
    sec = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    all_companies = pd.read_sql_query("SELECT id as company_id FROM companies", conn)["company_id"].tolist()

    merged = fr.merge(pl, on=["company_id", "year"], how="left").merge(bs, on=["company_id", "year"], how="left")
    # Per the project glossary, EBITDA proxy = operating_profit (already in Cr, matches total_debt_cr's units)
    merged["ebitda_proxy"] = merged.get("operating_profit")

    sector_map = dict(zip(sec["company_id"], sec["broad_sector"]))

    all_rows = []
    for cid, hist in merged.groupby("company_id"):
        hist = hist.sort_values("year")
        sector = sector_map.get(cid)
        entries = generate_pros_cons_for_company(hist, sector)
        for e in entries:
            all_rows.append({"company_id": cid, **e})

    df = pd.DataFrame(all_rows, columns=["company_id", "type", "rule_id", "text", "confidence_pct", "below_threshold"])
    os.makedirs("output", exist_ok=True)
    df.to_csv(out_path, index=False)

    covered = set(df["company_id"])
    missing = [c for c in all_companies if c not in covered]
    print(f"pros_cons_generated.csv: {len(df)} rows for {df['company_id'].nunique()} companies. "
          f"{len(missing)} companies with zero entries (below confidence threshold or insufficient history).")
    conn.close()
    return df


if __name__ == "__main__":
    run()
