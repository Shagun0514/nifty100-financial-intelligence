"""Sector report PDF generator — Sprint 5, Day 34. One PDF per broad_sector."""
import os
import sqlite3
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

DB_PATH = os.getenv("DB_PATH", "nifty100.db")
OUT_DIR = "reports/sector"
NAVY = colors.HexColor("#1F3864")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleWhite", parent=styles["Title"], textColor=colors.white, fontSize=18)
cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, wordWrap="CJK")
header_cell_style = ParagraphStyle("HeaderCell", parent=styles["Normal"], fontSize=8, textColor=colors.white,
                                    wordWrap="CJK")


def _fmt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.1f}"


def _header_bar(sector_name):
    t = Table([[Paragraph(sector_name, title_style)]], colWidths=[17 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                           ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                           ("LEFTPADDING", (0, 0), (-1, -1), 14)]))
    return t


METRICS = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
           "debt_to_equity", "interest_coverage", "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr"]
METRIC_LABELS = ["ROE%", "ROCE%", "NPM%", "D/E", "ICR", "FCF(Cr)", "RevCAGR5y%", "PATCAGR5y%"]


def build_sector_report(sector_name, companies_df, ratios_df, path):
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=1 * cm, bottomMargin=1 * cm,
                             leftMargin=1 * cm, rightMargin=1 * cm)
    story = [_header_bar(sector_name), Spacer(1, 14)]

    merged = ratios_df.merge(companies_df, on="company_id", how="inner")
    latest = merged.sort_values("year").groupby("company_id").tail(1)

    medians = latest[METRICS].median(numeric_only=True)
    median_row = [Paragraph("<b>Sector Median</b>", cell_style)] + [Paragraph(_fmt(medians.get(m)), cell_style)
                                                                     for m in METRICS]
    story.append(Paragraph(f"{sector_name} — {len(latest)} companies", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Table([median_row], colWidths=[3 * cm] + [1.7 * cm] * len(METRICS)))
    story.append(Spacer(1, 14))

    header = [Paragraph("<b>Ticker</b>", header_cell_style), Paragraph("<b>Company</b>", header_cell_style)] + \
              [Paragraph(f"<b>{lbl}</b>", header_cell_style) for lbl in METRIC_LABELS]
    table_data = [header]
    for _, row in latest.sort_values("company_name").iterrows():
        table_data.append([
            Paragraph(row["company_id"], cell_style), Paragraph(str(row.get("company_name", ""))[:25], cell_style),
        ] + [Paragraph(_fmt(row.get(m)), cell_style) for m in METRICS])

    col_widths = [1.8 * cm, 3.2 * cm] + [1.6 * cm] * len(METRICS)
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]))
    story.append(t)
    doc.build(story)
    return path


def generate_all_sector_reports(db_path=None, out_dir=OUT_DIR):
    conn = sqlite3.connect(db_path or DB_PATH)
    companies = pd.read_sql_query(
        "SELECT c.id as company_id, c.company_name, s.broad_sector FROM companies c "
        "LEFT JOIN sectors s ON s.company_id=c.id", conn)
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()

    os.makedirs(out_dir, exist_ok=True)
    written = []
    for sector_name, group in companies.groupby("broad_sector"):
        if pd.isna(sector_name):
            continue
        safe_name = sector_name.replace("/", "-").replace(" ", "_")
        path = os.path.join(out_dir, f"{safe_name}_report.pdf")
        build_sector_report(sector_name, group, ratios, path)
        written.append(path)

    print(f"Generated {len(written)} sector reports in {out_dir}/")
    return written


if __name__ == "__main__":
    generate_all_sector_reports()
