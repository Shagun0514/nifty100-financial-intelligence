.PHONY: setup load ratios test report dashboard api clean

setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

load:
	./venv/bin/python -m src.etl.loader

ratios:
	./venv/bin/python -m src.etl.ratios

test:
	./venv/bin/pytest tests/ -v

report:
	./venv/bin/python -m src.etl.validator > output/validation_failures.csv

dashboard:
	echo "dashboard target placeholder - Sprint 3"

api:
	echo "api target placeholder - Sprint 4"

clean:
	rm -f nifty100.db
	rm -f output/*.csv
