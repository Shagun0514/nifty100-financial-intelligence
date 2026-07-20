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

## If a load looks wrong
Open `output/load_audit.csv` — it shows rows_read/loaded/rejected per file.
If a file's real column headers differ slightly from the spec, open that one Excel file,
check the header row, and tell me the actual column names — I'll adjust the loader.

## Day-by-day (what's left for you)
- Day 01–04: done (env, loader, normaliser, schema)
- Day 05: `make load` — check counts: companies=92, P&L~1276, BS~1312, CF~1187, stock_prices=5520
- Day 06: eyeball 5 companies in `nifty100.db`; fix loader if columns don't match; re-run
- Day 07: `make test`, review `output/*.csv`, done
