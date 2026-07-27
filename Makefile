.PHONY: setup load ratios test report dashboard api clean

setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

load:
	./venv/bin/python -m src.etl.loader

ratios:
	./venv/bin/python -m src.analytics.populate_ratios

screener:
	./venv/bin/python -m src.screener.engine

peers:
	./venv/bin/python -m src.analytics.peer
	./venv/bin/python -m src.reports.peer_comparison_export

radar:
	./venv/bin/python -m src.reports.radar_charts

valuation:
	./venv/bin/python -m src.analytics.valuation

dashboard:
	./venv/bin/streamlit run src/dashboard/app.py

nlp:
	./venv/bin/python -m src.nlp.parser
	./venv/bin/python -m src.nlp.pros_cons_generator

cashflow:
	./venv/bin/python -m src.analytics.cashflow_intelligence

tearsheets:
	./venv/bin/python -m src.reports.tearsheet

sector-reports:
	./venv/bin/python -m src.reports.sector_report

portfolio:
	./venv/bin/python -m src.reports.portfolio_summary

clustering:
	./venv/bin/python -m src.analytics.clustering

portfolio-stats:
	./venv/bin/python -m src.analytics.portfolio_stats

api:
	./venv/bin/uvicorn src.api.main:app --port 8000

openapi:
	./venv/bin/python -m src.api.export_openapi
	./venv/bin/python -m src.api.export_postman

loadtest:
	./venv/bin/python -m src.api.load_test

analyst-guide:
	./venv/bin/python -m src.reports.analyst_guide

acceptance:
	./venv/bin/python -m src.reports.acceptance_checklist

test:
	./venv/bin/pytest tests/ -v

test-html:
	./venv/bin/pytest tests/ --html=reports/pytest_report.html --self-contained-html

report:
	./venv/bin/python -m src.etl.validator

dashboard:
	echo "dashboard target placeholder - Sprint 3"

api:
	echo "api target placeholder - Sprint 4"

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -f .pytest_cache -r
	rm -f output/*.csv output/*.log
	# NOTE: nifty100.db is intentionally NOT removed here — database remains untouched
