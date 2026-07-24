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

test:
	./venv/bin/pytest tests/ -v

report:
	./venv/bin/python -m src.etl.validator

dashboard:
	echo "dashboard target placeholder - Sprint 3"

api:
	echo "api target placeholder - Sprint 4"

clean:
	rm -f nifty100.db
	rm -f output/*.csv
