@echo off
REM ============================================================
REM  Nifty 100 Financial Intelligence Platform
REM  Full pipeline: Sprint 1 -> Sprint 6, all 23 deliverables
REM  Run from the project root: run_all.bat
REM ============================================================

echo.
echo === Sprint 1: Data Foundation ===
venv\Scripts\python -m src.etl.loader
venv\Scripts\python -m src.etl.validator

echo.
echo === Sprint 2: Financial Ratio Engine ===
venv\Scripts\python -m src.analytics.populate_ratios

echo.
echo === Sprint 3: Screener + Peer Comparison ===
venv\Scripts\python -m src.screener.engine
venv\Scripts\python -m src.analytics.peer
venv\Scripts\python -m src.reports.peer_comparison_export
venv\Scripts\python -m src.reports.radar_charts

echo.
echo === Sprint 4: Valuation ===
venv\Scripts\python -m src.analytics.valuation

echo.
echo === Sprint 5: NLP + Cash Flow Intelligence + PDF Reports ===
venv\Scripts\python -m src.nlp.parser
venv\Scripts\python -m src.nlp.pros_cons_generator
venv\Scripts\python -m src.analytics.cashflow_intelligence
venv\Scripts\python -m src.reports.tearsheet
venv\Scripts\python -m src.reports.sector_report
venv\Scripts\python -m src.reports.portfolio_summary

echo.
echo === Sprint 6: Clustering + API docs + Final QA ===
venv\Scripts\python -m src.analytics.clustering
venv\Scripts\python -m src.analytics.portfolio_stats
venv\Scripts\python -m src.api.export_openapi
venv\Scripts\python -m src.api.export_postman
venv\Scripts\python -m src.reports.analyst_guide

echo.
echo === Running full test suite with HTML report ===
venv\Scripts\python -m pytest tests\ --html=reports\pytest_report.html --self-contained-html -v

echo.
echo === Final acceptance checklist ===
venv\Scripts\python -m src.reports.acceptance_checklist

echo.
echo ============================================================
echo  Pipeline complete. Check these for final review:
echo    docs\acceptance_checklist.pdf   - 20 gate results
echo    reports\pytest_report.html      - full test results
echo    docs\analyst_guide.pdf          - user guide
echo.
echo  Then, in separate terminals:
echo    venv\Scripts\streamlit run src\dashboard\app.py     (port 8501)
echo    venv\Scripts\uvicorn src.api.main:app --port 8000    (port 8000)
echo ============================================================
