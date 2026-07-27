"""Generates docs/analyst_guide.pdf — Sprint 6, Day 44. 10+ pages."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 PageBreak, ListFlowable, ListItem)

NAVY = colors.HexColor("#1F3864")
styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleWhite", parent=styles["Title"], textColor=colors.white, fontSize=22)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], spaceBefore=14, textColor=NAVY)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=10)
body = ParagraphStyle("Body", parent=styles["Normal"], spaceAfter=8, wordWrap="CJK")
code = ParagraphStyle("Code", parent=styles["Normal"], fontName="Courier", fontSize=9,
                       backColor=colors.HexColor("#F2F2F2"), leftIndent=10, spaceAfter=8, wordWrap="CJK")


def _cover_page():
    return [Spacer(1, 6 * cm),
            Table([[Paragraph("Nifty 100 Financial Intelligence Platform", title_style)]],
                  colWidths=[17 * cm], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                                                          ("TOPPADDING", (0, 0), (-1, -1), 20),
                                                          ("BOTTOMPADDING", (0, 0), (-1, -1), 20)])),
            Spacer(1, 1 * cm),
            Paragraph("Analyst Guide", ParagraphStyle("Sub", parent=styles["Heading2"], alignment=1)),
            Spacer(1, 0.3 * cm),
            Paragraph("Version 1.0 — Sprint 6", ParagraphStyle("Sub2", parent=styles["Normal"], alignment=1)),
            PageBreak()]


def _section(title, paragraphs):
    flow = [Paragraph(title, h1)]
    for p in paragraphs:
        if isinstance(p, tuple) and p[0] == "code":
            flow.append(Paragraph(p[1], code))
        elif isinstance(p, tuple) and p[0] == "h2":
            flow.append(Paragraph(p[1], h2))
        elif isinstance(p, tuple) and p[0] == "list":
            flow.append(ListFlowable([ListItem(Paragraph(item, body)) for item in p[1]], bulletType="bullet"))
        else:
            flow.append(Paragraph(p, body))
    return flow


def build_analyst_guide(path="docs/analyst_guide.pdf"):
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    story = _cover_page()

    story += _section("1. Overview", [
        "The Nifty 100 Financial Intelligence Platform is a self-contained analytics system covering "
        "92 Nifty 100 companies across 12 years of financial history. It combines a validated SQLite "
        "database, a computed ratio engine, an investment screener, peer comparison tools, automated "
        "PDF reporting, a Streamlit dashboard, and a REST API.",
        ("h2", "What this guide covers"),
        ("list", ["Using the Streamlit screener and dashboard screens",
                  "Navigating each of the 8 dashboard screens",
                  "Generating PDF tearsheets and reports",
                  "Calling the REST API with example commands",
                  "Troubleshooting common issues"]),
    ])
    story.append(PageBreak())

    story += _section("2. Getting Started", [
        "All commands below assume you're in the project's root folder with the virtual environment activated.",
        ("h2", "First-time setup"),
        ("code", "python -m venv venv<br/>venv\\Scripts\\pip install -r requirements.txt<br/>"
                  "copy .env.example .env"),
        ("h2", "Build the database"),
        ("code", "venv\\Scripts\\python -m src.etl.loader<br/>"
                  "venv\\Scripts\\python -m src.analytics.populate_ratios"),
        "This must be run before anything else — every downstream module (screener, dashboard, API) "
        "reads from the resulting nifty100.db file.",
    ])
    story.append(PageBreak())

    story += _section("3. Using the Streamlit Screener", [
        "Launch the dashboard with:",
        ("code", "venv\\Scripts\\streamlit run src\\dashboard\\app.py"),
        "Navigate to the Screener page from the sidebar. Ten sliders let you set thresholds for ROE, "
        "debt-to-equity, free cash flow, revenue and profit growth, margins, valuation multiples, "
        "dividend yield, and interest coverage.",
        ("h2", "Using presets"),
        "Six preset buttons — Quality, Value, Growth, Dividend, Debt-Free, and Turnaround — auto-fill "
        "the sliders to match a known investment style. You can still fine-tune any slider afterward.",
        ("h2", "Exporting results"),
        "The Download CSV button exports exactly what's shown in the results table, including the "
        "composite quality score column.",
    ])
    story.append(PageBreak())

    story += _section("4. Navigating the Dashboard", [
        "The dashboard has 8 screens, accessible from the sidebar:",
        ("list", [
            "<b>Home</b> — portfolio-wide KPI tiles, sector donut chart, top 5 by composite score, year selector",
            "<b>Profile</b> — search any company for its KPIs, 10-year charts, and pros/cons",
            "<b>Screener</b> — see Section 3",
            "<b>Peers</b> — radar chart of a company vs its peer group average, side-by-side table",
            "<b>Trends</b> — overlay up to 3 metrics for one company with YoY % change labels",
            "<b>Sectors</b> — bubble chart (Revenue x ROE, sized by market cap) plus median KPI bars",
            "<b>Capital</b> — treemap of all companies by capital allocation pattern",
            "<b>Reports</b> — annual report links per company, with an on-demand dead-link check",
        ]),
    ])
    story.append(PageBreak())

    story += _section("5. Generating PDF Reports", [
        "Three types of PDF reports can be generated from the command line:",
        ("h2", "Company tearsheets (2 pages, one per company)"),
        ("code", "venv\\Scripts\\python -m src.reports.tearsheet"),
        "Companies with fewer than 3 years of P&L history are skipped and logged to "
        "output/skipped_tearsheets.csv — this is expected, not an error.",
        ("h2", "Sector reports (one per broad sector)"),
        ("code", "venv\\Scripts\\python -m src.reports.sector_report"),
        ("h2", "Portfolio summary (one page per company)"),
        ("code", "venv\\Scripts\\python -m src.reports.portfolio_summary"),
        "Each page shows a company's top 6 KPIs with a colour-coded UP/DOWN/FLAT trend label versus "
        "the prior year.",
    ])
    story.append(PageBreak())

    story += _section("6. Using the REST API", [
        "Start the API server with:",
        ("code", "venv\\Scripts\\uvicorn src.api.main:app --port 8000"),
        "Interactive documentation is available at http://localhost:8000/docs — every endpoint can be "
        "tried directly from the browser.",
        ("h2", "Example: get a company's ratio history"),
        ("code", 'curl "http://localhost:8000/api/v1/companies/TCS/ratios"'),
        ("h2", "Example: run the screener via the API"),
        ("code", 'curl "http://localhost:8000/api/v1/screener?min_roe=15&max_de=1"'),
        ("h2", "Example: download a tearsheet"),
        ("code", 'curl "http://localhost:8000/api/v1/companies/TCS/tearsheet" --output tcs.pdf'),
        "All 16 endpoints are documented in docs/openapi.json and can be imported into Postman via "
        "docs/postman_collection.json.",
    ])
    story.append(PageBreak())

    story += _section("7. Understanding the Data", [
        "A few things worth knowing before drawing conclusions from the numbers:",
        ("list", [
            "The dataset covers 92 of the 100 Nifty 100 companies — 8 were excluded during data "
            "collection for availability reasons.",
            "Rows labelled 'TTM' (Trailing Twelve Months) in the source data are intentionally excluded "
            "from annual tables, since they aren't a complete fiscal year.",
            "The sector taxonomy has 10 broad sectors in the actual dataset, not the 11 originally "
            "anticipated — the 'Conglomerates/Other' category isn't present in the source file.",
            "market_cap.xlsx and stock_prices.xlsx are simulated data, clearly labelled as such — don't "
            "draw real investment conclusions from valuation multiples or price charts.",
            "CON-11 in the auto-generated pros/cons ('Net Debt > 3x EBITDA') uses operating_profit as "
            "an EBITDA proxy, per this project's own glossary definition.",
        ]),
    ])
    story.append(PageBreak())

    story += _section("8. Troubleshooting", [
        ("h2", "\"Database not found\" errors"),
        "Run `make load` (or the manual loader command) first — every other module depends on "
        "nifty100.db existing.",
        ("h2", "Dashboard shows 'N/A' for a company"),
        "This is expected for companies with partial data coverage — it means that specific metric "
        "couldn't be computed (e.g. division by zero, or a missing source value), not a bug.",
        ("h2", "Port already in use"),
        "The dashboard defaults to port 8501, the API to port 8000. If either is already running "
        "elsewhere on your machine, stop that process or specify a different port "
        "(--server.port for Streamlit, --port for uvicorn).",
        ("h2", "Tests failing after a fresh clone"),
        "Make sure you've run `pip install -r requirements.txt` inside your virtual environment, and "
        "that you're running pytest from the project root, not a subfolder.",
        ("h2", "Getting help"),
        "Check output/load_audit.csv and output/validation_failures.csv first — most data-related "
        "questions are answered by what's already logged there.",
    ])
    story.append(PageBreak())

    story += _section("9. Project Architecture Summary", [
        "For reference, here's how the six build sprints fit together:",
        ("list", [
            "<b>Sprint 1 — Data Foundation:</b> loads 12 source Excel files into a validated 12-table "
            "SQLite database, enforcing 16 data quality rules.",
            "<b>Sprint 2 — Ratio Engine:</b> computes 50+ financial ratios per company-year, including "
            "CAGR growth metrics and capital allocation classification.",
            "<b>Sprint 3 — Screener & Peers:</b> 6 preset screeners plus custom filtering, and percentile "
            "ranking within 11 peer groups.",
            "<b>Sprint 4 — Dashboard & Valuation:</b> an 8-screen Streamlit app and a valuation module "
            "flagging over/undervalued companies vs sector medians.",
            "<b>Sprint 5 — NLP & Reports:</b> auto-generated pros/cons (24 rules), cash flow intelligence "
            "scoring, and automated PDF tearsheets, sector reports, and portfolio summaries.",
            "<b>Sprint 6 — Clustering, API & QA:</b> KMeans company archetypes, a 16-endpoint REST API, "
            "and this documentation.",
        ]),
        ("h2", "Where things live"),
        ("code", "src/etl/       - loading, normalising, validating source data<br/>"
                  "src/analytics/ - ratio engine, screener scoring, clustering, valuation<br/>"
                  "src/nlp/       - text parsing and rule-based insight generation<br/>"
                  "src/reports/   - PDF generation (tearsheets, sector, portfolio, this guide)<br/>"
                  "src/dashboard/ - Streamlit app and pages<br/>"
                  "src/api/       - FastAPI server and routers<br/>"
                  "tests/         - one folder per module area, 170+ tests total"),
    ])

    doc.build(story)
    return path


if __name__ == "__main__":
    path = build_analyst_guide()
    print(f"analyst_guide.pdf written to {path}")
