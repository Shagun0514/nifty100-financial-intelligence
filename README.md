# Nifty 100 Financial Intelligence Platform

A complete financial analytics platform for 92 Nifty 100 companies: a validated SQLite
database, a 50+ KPI ratio engine, an investment screener, peer comparison, an 8-screen
Streamlit dashboard, automated PDF reporting, KMeans company clustering, and a 16-endpoint
REST API — built across 6 sprints, 170+ passing tests.

## Full pipeline, start to finish
```
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env

venv\Scripts\python -m src.etl.loader              REM Sprint 1: build the database
venv\Scripts\python -m src.analytics.populate_ratios REM Sprint 2: compute 50+ KPIs
venv\Scripts\python -m src.screener.engine          REM Sprint 3: screener + composite scores
venv\Scripts\python -m src.analytics.peer            REM Sprint 3: peer percentiles
venv\Scripts\python -m src.analytics.valuation       REM Sprint 4: valuation flags
venv\Scripts\python -m src.nlp.pros_cons_generator   REM Sprint 5: auto pros/cons
venv\Scripts\python -m src.analytics.cashflow_intelligence REM Sprint 5: cash flow scoring
venv\Scripts\python -m src.reports.tearsheet         REM Sprint 5: 91 tearsheet PDFs
venv\Scripts\python -m src.analytics.clustering      REM Sprint 6: KMeans archetypes

venv\Scripts\python -m pytest tests\ -v              REM 170+ tests, should all pass
venv\Scripts\streamlit run src\dashboard\app.py       REM interactive dashboard, port 8501
venv\Scripts\uvicorn src.api.main:app --port 8000     REM REST API, docs at /docs
```
Each sprint section below has the full detail and additional outputs for that stage.

---

# Sprint 1 – Data Foundation (nifty100.db)

Matches your uploaded spec (`Nifty100_Project_Document_FINAL.pdf`) and Drive folders
("Datasets" + "Supporting Datasets").

> **Note:** This repo does NOT include the source `.xlsx` data files, the built
> `nifty100.db`, or `.env` (see `.gitignore`) — they're excluded on purpose since
> the data is licensed/private and the database is just a build artifact.
> To run this yourself: copy `.env.example` to `.env`, add your own 12 Excel
> files as described below, then run `make load` (or the manual commands in
> the Quick-Start section) to regenerate `nifty100.db` locally.

## Where to put your 12 files
```
data/raw/companies.xlsx
data/raw/profitandloss.xlsx
data/raw/balancesheet.xlsx
data/raw/cashflow.xlsx
data/raw/analysis.xlsx
data/raw/documents.xlsx
data/raw/prosandcons.xlsx

data/supporting/sectors.xlsx
data/supporting/stock_prices.xlsx
data/supporting/market_cap.xlsx
data/supporting/financial_ratios.xlsx
data/supporting/peer_groups.xlsx
```
Just download these straight from your two Drive folders into those two directories —
filenames already match, no renaming needed.

**Important:** the 7 core files have a metadata row above the real header
(spec says `header=1`); the loader already handles this. Supplementary files load with `header=0`.

## Steps
```bash
cd nifty100_etl
make setup            # venv + 20 libraries
cp .env.example .env
make load              # loads all 12 files -> nifty100.db, output/load_audit.csv
make report            # runs 16 DQ rules -> output/validation_failures.csv
make test              # runs 52 unit tests
```

## Definition of Done (from the spec, Sprint 1 exit criteria)
```bash
sqlite3 nifty100.db "SELECT COUNT(*) FROM companies;"   -- should be 92
sqlite3 nifty100.db "PRAGMA foreign_key_check;"          -- should print nothing
```
- `output/load_audit.csv` → 0 rows with a CRITICAL error
- `output/validation_failures.csv` → 0 rows with severity CRITICAL (DQ-01,02,03,07,08 are CRITICAL)
- `make test` → all pass

## What's already built
- `db/schema.sql` – 12 tables (7 core + 5 supplementary), real column names from the spec, PK/FK, done
- `src/etl/normaliser.py` – `normalize_year()` → `'YYYY-MM'` (Mar-23→2023-03), `normalize_ticker()`, done
- `src/etl/loader.py` – loads all 12 files, handles the `header=1` quirk, expands `peer_groups.xlsx` (Members column) into rows
- `src/etl/validator.py` – all 16 DQ rules (DQ-01…DQ-16) exactly as listed in the spec's Section 14
- `tests/etl/` – 52 unit tests, all passing already
- `notebooks/exploratory_queries.sql` – 10 queries matching the real schema

## Sprint 4 — Dashboard & Valuation

### Run the dashboard
```
make dashboard
```
(or manually: `venv\Scripts\streamlit run src\dashboard\app.py`)

Opens at `http://localhost:8501`. Requires `nifty100.db` to already exist (`make load`)
with ratios (`make ratios`), peer data (`make peers`), and valuation (`make valuation`)
populated for full functionality — pages degrade gracefully with a warning message
if a dependency hasn't been run yet, rather than crashing.

### The 8 screens
1. **Home** — portfolio-wide KPI tiles (avg ROE, median D/E, debt-free count, etc.), sector
   breakdown donut chart, top-5 companies by composite quality score, year selector.
2. **Profile** — search any company, see its KPI tiles, 10-year revenue/profit bar chart,
   ROE/ROCE dual-axis line chart, and pros/cons as green/red badges.
3. **Screener** — 10 sidebar sliders plus 6 one-click presets (Quality, Value, Growth,
   Dividend, Debt-Free, Turnaround), live-updating results table, CSV download.
4. **Peers** — pick a peer group and a company, see an 8-axis radar chart vs the peer
   group average, plus a side-by-side table with the benchmark company highlighted.
5. **Trends** — overlay up to 3 metrics for one company over 10 years, with YoY % change
   labels on each point.
6. **Sectors** — bubble chart (Revenue x ROE, bubble size = market cap) for a chosen
   sector, plus a sector median KPI bar chart.
7. **Capital** — treemap of all companies by capital allocation pattern (Reinvestor,
   Distress Signal, etc.), with drill-down by pattern.
8. **Reports** — annual report links per company, year by year, with an on-demand
   "Check link" button that flags dead links (not checked automatically, for speed).

### Valuation module
```
make valuation
```
Writes `output/valuation_summary.xlsx` (all companies, P/E, P/B, EV/EBITDA, FCF yield,
5yr median P/E, and a Caution/Discount/Fair flag vs sector median P/E) and
`output/valuation_flags.csv` (only the flagged companies).


Open `output/load_audit.csv` — it shows rows_read/loaded/rejected per file.
If a file's real column headers differ slightly from the spec, open that one Excel file,
check the header row, and tell me the actual column names — I'll adjust the loader.

## Sprint 5 — NLP, Cash Flow Intelligence & PDF Reports

### Run everything
```
make nlp             # analysis_parsed.csv, parse_failures.csv, pros_cons_generated.csv
make cashflow         # cashflow_intelligence.xlsx, distress_alerts.csv, pattern_changes.csv
make tearsheets       # 92 x 2-page company PDFs -> reports/tearsheets/
make sector-reports   # 11 sector PDFs -> reports/sector/
make portfolio        # 1 PDF, one page per company -> reports/portfolio/
```
Run `make ratios` first if you haven't — cash flow intelligence and tearsheets both
depend on `financial_ratios` and `capital_allocation.csv` from Sprint 2.

### What each piece does
- **NLP parser** (`src/nlp/parser.py`) — extracts `(period_years, value_pct)` from free-text
  fields in `analysis.xlsx` like `"10 Years: 21%"`, and flags entries where the parsed
  value diverges >5% from the Ratio Engine's own computed CAGR.
- **Pros/cons generator** (`src/nlp/pros_cons_generator.py`) — 12 pro rules + 12 con rules
  (high ROE, debt-free, declining margins, net loss, etc.), each with a confidence score;
  only entries above 60% confidence are kept.
- **Cash Flow Intelligence** (`src/analytics/cashflow_intelligence.py`) — CFO quality score
  (High Quality / Moderate / Accrual Risk), CapEx intensity (Asset Light / Moderate /
  Capital Intensive), distress signal (CFO<0 and CFF>0), deleveraging flag (CFF<0 and
  falling debt), and year-over-year capital allocation pattern changes.
- **Tearsheets** (`src/reports/tearsheet.py`) — 2-page PDF per company: navy header, 6 KPI
  tiles, revenue/profit and ROE/ROCE charts on page 1; balance sheet composition, cash flow
  waterfall, pros/cons, and capital allocation badge on page 2. Companies with fewer than
  3 years of P&L history are skipped and logged to `output/skipped_tearsheets.csv`.
- **Sector reports** (`src/reports/sector_report.py`) — one PDF per broad sector: median
  KPI row + every company in that sector with 8 metrics.
  **Known data note:** generates 10 PDFs, not 11. The spec anticipated 11 broad sectors
  including "Conglomerates/Other," but the actual `sectors.xlsx` file only contains 10
  distinct `broad_sector` values — that category isn't present in the real dataset. Not
  a bug; verified by checking the source file directly.
- **Portfolio summary** (`src/reports/portfolio_summary.py`) — one page per company,
  alphabetical by ticker, top 6 KPIs with a trend arrow (↑/↓/→, ±2% flat threshold).

**Documented approximation:** CON-11 ("Net Debt > 3x EBITDA") uses `operating_profit`
as the EBITDA proxy, matching this project's own glossary definition — there's no
separately reported EBITDA field in the source data.

## Sprint 6 — Clustering, REST API & Final QA

### Run everything
```
make clustering       # KMeans -> output/cluster_labels.csv, reports/elbow_plot.png
make portfolio-stats   # correlation heatmap, outlier report, P10-P90 stats
make api               # starts FastAPI on localhost:8000 (docs at /docs)
make openapi           # exports docs/openapi.json + docs/postman_collection.json
make loadtest          # 10 concurrent screener requests -> output/perf_notes.md
make analyst-guide     # docs/analyst_guide.pdf (10+ pages)
make acceptance        # runs all 20 acceptance gates -> docs/acceptance_checklist.pdf
make test-html         # pytest with HTML report -> reports/pytest_report.html
```

### What's new
- **Clustering** (`src/analytics/clustering.py`) — KMeans, 5 clusters, features imputed by
  sector median before scaling. Cluster names are assigned by simple rule-based heuristics
  (e.g. high ROE + low debt + growth → "High-Quality Compounders"); per the original spec,
  these names are meant to be reviewed and adjusted by a human once you see which actual
  companies land in each cluster — one cluster may fall through to a generic "Cluster N"
  label if none of the heuristic rules match its profile, which is expected, not a bug.
- **Portfolio stats** (`src/analytics/portfolio_stats.py`) — correlation heatmap (10 KPIs),
  per-sector Z-score outlier detection, P10-P90 percentile table.
- **REST API** (`src/api/`) — FastAPI server, 16 endpoints across 8 routers (health,
  companies, screener, sectors, peers, valuation, portfolio, documents), CORS enabled,
  request-logging middleware, and a custom handler that returns HTTP 400 (not FastAPI's
  default 422) for invalid query parameters, matching the spec.
- **Acceptance checklist** (`src/reports/acceptance_checklist.py`) — programmatically
  re-verifies as many of the 20 acceptance gates as can be checked automatically (row
  counts, FK integrity, file existence, API health, test suite status) and generates a
  colour-coded PDF. A handful of gates (CAGR spot-checks, visual PDF review, dashboard
  load-time) are inherently manual and are marked "MANUAL CHECK" rather than guessed at.

### Known, documented gaps (carried from earlier sprints, still accurate)
- 92 of 100 Nifty 100 companies (data availability filter applied upstream)
- 10 broad sectors in the actual data, not 11 (no "Conglomerates/Other" category present)
- TTM (Trailing Twelve Months) rows correctly excluded from annual tables throughout

## Day-by-day (what's left for you)
- Day 01–04: done (env, loader, normaliser, schema)
- Day 05: `make load` — check counts: companies=92, P&L~1276, BS~1312, CF~1187, stock_prices=5520
- Day 06: eyeball 5 companies in `nifty100.db`; fix loader if columns don't match; re-run
- Day 07: `make test`, review `output/*.csv`, done
