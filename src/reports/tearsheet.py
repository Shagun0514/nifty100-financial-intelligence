"""Company tearsheet PDF generator — Sprint 5, Day 33-34.
2 pages per company: KPIs + charts (page 1), balance sheet/cash flow/pros-cons (page 2).
"""
import os
import csv
import sqlite3
import io
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 Image, PageBreak, KeepTogether)

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
OUT_DIR = "reports/tearsheets"
NAVY = colors.HexColor("#1F3864")
MIN_YEARS = 3

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleWhite", parent=styles["Title"], textColor=colors.white, fontSize=20)
sub_style = ParagraphStyle("SubWhite", parent=styles["Normal"], textColor=colors.white, fontSize=11)
section_style = ParagraphStyle("Section", parent=styles["Heading2"], spaceBefore=10)
body_style = ParagraphStyle("Body", parent=styles["Normal"], wordWrap="CJK")  # wrap long text safely
pro_style = ParagraphStyle("Pro", parent=styles["Normal"], textColor=colors.HexColor("#2E7D32"), wordWrap="CJK")
con_style = ParagraphStyle("Con", parent=styles["Normal"], textColor=colors.HexColor("#C62828"), wordWrap="CJK")


def _fmt(v, suffix=""):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.1f}{suffix}"


def _fig_to_image(fig, width=8 * cm, height=6 * cm):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def _header_bar(name, ticker):
    data = [[Paragraph(f"{name} ({ticker})", title_style)]]
    t = Table(data, colWidths=[17 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return t


def _kpi_tiles(kpis):
    """kpis: list of (label, value) tuples, laid out 3 per row."""
    rows, row = [], []
    for i, (label, value) in enumerate(kpis):
        cell = Paragraph(f"<b>{label}</b><br/>{value}", body_style)
        row.append(cell)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        while len(row) < 3:
            row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[5.6 * cm] * 3)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F2F2")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def build_tearsheet(company_id, data, path):
    """data: dict with keys company_name, sector, ratios (df), pl (df), bs (df), cf (df),
    pros (list), cons (list), capital_allocation_label (str)."""
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=1 * cm, bottomMargin=1 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    story = [_header_bar(data["company_name"], company_id), Spacer(1, 14)]

    ratios = data["ratios"].sort_values("year")
    latest = ratios.iloc[-1] if not ratios.empty else pd.Series(dtype=float)
    kpis = [
        ("ROE", _fmt(latest.get("return_on_equity_pct"), "%")),
        ("ROCE", _fmt(latest.get("return_on_capital_employed_pct"), "%")),
        ("Net Profit Margin", _fmt(latest.get("net_profit_margin_pct"), "%")),
        ("D/E", _fmt(latest.get("debt_to_equity"))),
        ("Revenue CAGR 5yr", _fmt(latest.get("revenue_cagr_5yr"), "%")),
        ("Free Cash Flow (Cr)", _fmt(latest.get("free_cash_flow_cr"))),
    ]
    story.append(_kpi_tiles(kpis))
    story.append(Spacer(1, 14))

    pl = data["pl"].sort_values("year").tail(10)
    if not pl.empty:
        fig, ax = plt.subplots(figsize=(6, 3.2))
        x = range(len(pl))
        ax.bar([i - 0.2 for i in x], pl["sales"], width=0.4, label="Revenue")
        ax.bar([i + 0.2 for i in x], pl["net_profit"], width=0.4, label="Net Profit")
        ax.set_xticks(list(x))
        ax.set_xticklabels(pl["year"], rotation=45, fontsize=7)
        ax.legend(fontsize=8)
        ax.set_title("Revenue & Net Profit (Cr)", fontsize=10)
        fig.tight_layout()
        story.append(Paragraph("Revenue & Net Profit (10yr)", section_style))
        story.append(_fig_to_image(fig, width=16 * cm, height=7 * cm))

    r_recent = ratios.tail(10)
    if not r_recent.empty:
        fig2, ax1 = plt.subplots(figsize=(6, 3.2))
        ax2 = ax1.twinx()
        ax1.plot(r_recent["year"], r_recent["return_on_equity_pct"], color="tab:blue", label="ROE")
        ax2.plot(r_recent["year"], r_recent["return_on_capital_employed_pct"], color="tab:orange", label="ROCE")
        ax1.set_xticks(range(len(r_recent)))
        ax1.set_xticklabels(r_recent["year"], rotation=45, fontsize=7)
        ax1.set_ylabel("ROE (%)", color="tab:blue")
        ax2.set_ylabel("ROCE (%)", color="tab:orange")
        fig2.tight_layout()
        story.append(Spacer(1, 10))
        story.append(Paragraph("ROE & ROCE (10yr)", section_style))
        story.append(_fig_to_image(fig2, width=16 * cm, height=7 * cm))

    story.append(PageBreak())

    bs = data["bs"].sort_values("year").tail(10)
    if not bs.empty:
        fig3, ax = plt.subplots(figsize=(6, 3.2))
        ax.bar(bs["year"], bs["equity_capital"].fillna(0) + bs["reserves"].fillna(0), label="Equity")
        bottom1 = bs["equity_capital"].fillna(0) + bs["reserves"].fillna(0)
        ax.bar(bs["year"], bs["borrowings"].fillna(0), bottom=bottom1, label="Borrowings")
        bottom2 = bottom1 + bs["borrowings"].fillna(0)
        ax.bar(bs["year"], bs["other_liabilities"].fillna(0), bottom=bottom2, label="Other Liabilities")
        ax.set_xticks(range(len(bs)))
        ax.set_xticklabels(bs["year"], rotation=45, fontsize=7)
        ax.legend(fontsize=8)
        ax.set_title("Balance Sheet Composition (Cr)", fontsize=10)
        fig3.tight_layout()
        story.append(Paragraph("Balance Sheet Composition", section_style))
        story.append(_fig_to_image(fig3, width=16 * cm, height=7 * cm))

    cf = data["cf"].sort_values("year")
    if not cf.empty:
        latest_cf = cf.iloc[-1]
        fig4, ax = plt.subplots(figsize=(6, 3))
        labels = ["CFO", "CFI", "CFF", "Net"]
        vals = [latest_cf.get("operating_activity") or 0, latest_cf.get("investing_activity") or 0,
                latest_cf.get("financing_activity") or 0, latest_cf.get("net_cash_flow") or 0]
        colors_list = ["tab:green" if v >= 0 else "tab:red" for v in vals]
        ax.bar(labels, vals, color=colors_list)
        ax.set_title(f"Cash Flow Waterfall — {latest_cf['year']} (Cr)", fontsize=10)
        fig4.tight_layout()
        story.append(Spacer(1, 10))
        story.append(Paragraph("Cash Flow (Latest Year)", section_style))
        story.append(_fig_to_image(fig4, width=14 * cm, height=6 * cm))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Pros", section_style))
    for pro in data.get("pros", []) or ["No pros identified above confidence threshold."]:
        story.append(Paragraph(f"&#10003; {pro}", pro_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Cons", section_style))
    for con in data.get("cons", []) or ["No cons identified above confidence threshold."]:
        story.append(Paragraph(f"&#10007; {con}", con_style))

    if data.get("capital_allocation_label"):
        story.append(Spacer(1, 10))
        badge = Table([[Paragraph(f"Capital Allocation: {data['capital_allocation_label']}", body_style)]],
                       colWidths=[10 * cm])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3CD")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(badge)

    doc.build(story)
    return path


def _gather_company_data(conn, company_id):
    comp = pd.read_sql_query("SELECT company_name FROM companies WHERE id=?", conn, params=(company_id,))
    sec = pd.read_sql_query("SELECT broad_sector FROM sectors WHERE company_id=?", conn, params=(company_id,))
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios WHERE company_id=?", conn, params=(company_id,))
    pl = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id=?", conn, params=(company_id,))
    bs = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id=?", conn, params=(company_id,))
    cf = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id=?", conn, params=(company_id,))

    pros_cons_path = "output/pros_cons_generated.csv"
    pros, cons = [], []
    if os.path.exists(pros_cons_path):
        pc = pd.read_csv(pros_cons_path)
        pc = pc[pc["company_id"] == company_id]
        pros = pc[pc["type"] == "pro"]["text"].tolist()
        cons = pc[pc["type"] == "con"]["text"].tolist()

    capital_label = None
    ca_path = "output/capital_allocation.csv"
    if os.path.exists(ca_path):
        ca = pd.read_csv(ca_path)
        ca = ca[ca["company_id"] == company_id].sort_values("year")
        if not ca.empty:
            capital_label = ca.iloc[-1]["pattern_label"]

    return {
        "company_name": comp.iloc[0]["company_name"] if not comp.empty else company_id,
        "sector": sec.iloc[0]["broad_sector"] if not sec.empty else None,
        "ratios": ratios, "pl": pl, "bs": bs, "cf": cf, "pros": pros, "cons": cons,
        "capital_allocation_label": capital_label,
    }


def generate_all_tearsheets(db_path=None, out_dir=OUT_DIR):
    conn = sqlite3.connect(db_path or DB_PATH)
    companies = pd.read_sql_query("SELECT id FROM companies", conn)["id"].tolist()
    os.makedirs(out_dir, exist_ok=True)

    written, skipped = [], []
    for cid in companies:
        pl_years = conn.execute("SELECT COUNT(DISTINCT year) FROM profitandloss WHERE company_id=?",
                                 (cid,)).fetchone()[0]
        if pl_years < MIN_YEARS:
            skipped.append({"company_id": cid, "years_available": pl_years})
            continue
        data = _gather_company_data(conn, cid)
        path = os.path.join(out_dir, f"{cid}_tearsheet.pdf")
        try:
            build_tearsheet(cid, data, path)
            written.append(path)
        except Exception as e:
            skipped.append({"company_id": cid, "years_available": pl_years, "error": str(e)})

    os.makedirs("output", exist_ok=True)
    with open("output/skipped_tearsheets.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_id", "years_available", "error"])
        w.writeheader()
        for row in skipped:
            row.setdefault("error", "")
            w.writerow(row)

    print(f"Generated {len(written)} tearsheets. Skipped {len(skipped)} (see output/skipped_tearsheets.csv).")
    conn.close()
    return written, skipped


if __name__ == "__main__":
    generate_all_tearsheets()
