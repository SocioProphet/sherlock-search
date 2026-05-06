.PHONY: validate prophet-understand-smoke

validate: prophet-understand-smoke
	@echo "OK: sherlock-search validate"

prophet-understand-smoke:
	python3 tools/smoke_prophet_understanding_search.py
