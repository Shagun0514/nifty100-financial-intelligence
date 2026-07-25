"""Portfolio summary PDF — Sprint 5, Day 35. One page per company, alphabetical by ticker,
top 6 KPIs with YoY trend arrows (up if improved, down if declined, right if flat within 2%).
"""
import os
import sqlite3
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
OUT_PATH = "reports/portfolio/portfolio_summary.pdf"
NAVY = colors.HexColor("#1F3864")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleWhite", parent=styles["Title"], textColor=colors.white, fontSize=18)
cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=10)

METRICS = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
           "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr"]
METRIC_LABELS = ["ROE %", "ROCE %", "Net Profit Margin %", "D/E", "Free Cash Flow (Cr)", "Revenue CAGR 5yr %"]


def _arrow(curr, prev):
    """Returns (symbol, color) — ASCII-safe symbols since Unicode arrows (↑↓→) don't
    render reliably in every PDF viewer/font combination."""
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev) or prev == 0:
        return "FLAT", colors.grey
    change_pct = (curr - prev) / abs(prev) * 100
    if change_pct > 2:
        return "UP", colors.HexColor("#2E7D32")
    if change_pct < -2:
        return "DOWN", colors.HexColor("#C62828")
    return "FLAT", colors.grey


def _fmt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.1f}"


def build_portfolio_summary(db_path=None, out_path=OUT_PATH):
    conn = sqlite3.connect(db_path or DB_PATH)
    companies = pd.read_sql_query(
        "SELECT c.id as company_id, c.company_name, s.broad_sector FROM companies c "
        "LEFT JOIN sectors s ON s.company_id=c.id ORDER BY c.id", conn)
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()

    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    story = []

    for i, (_, row) in enumerate(companies.iterrows()):
        cid = row["company_id"]
        hist = ratios[ratios["company_id"] == cid].sort_values("year")
        if hist.empty:
            continue
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else pd.Series(dtype=float)

        header = Table([[Paragraph(f"{row['company_name']} ({cid})", title_style)]], colWidths=[16 * cm])
        header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                                     ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                                     ("LEFTPADDING", (0, 0), (-1, -1), 12)]))
        story.append(header)
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Sector: {row.get('broad_sector') or 'N/A'}", styles["Normal"]))
        story.append(Spacer(1, 12))

        table_data = [["Metric", "Latest Value", "Trend"]]
        for metric, label in zip(METRICS, METRIC_LABELS):
            curr_val = latest.get(metric)
            prev_val = prev.get(metric) if not prev.empty else None
            symbol, color = _arrow(curr_val, prev_val)
            trend_style = ParagraphStyle("Trend", parent=cell_style, textColor=color, alignment=1)
            table_data.append([label, _fmt(curr_val), Paragraph(f"<b>{symbol}</b>", trend_style)])

        t = Table(table_data, colWidths=[8 * cm, 5 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ]))
        story.append(t)

        if i < len(companies) - 1:
            story.append(PageBreak())

    dirname = os.path.dirname(out_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    doc.build(story)
    print(f"portfolio_summary.pdf: {len(companies)} companies.")
    return out_path


if __name__ == "__main__":
    build_portfolio_summary()
