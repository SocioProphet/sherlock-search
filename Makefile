.PHONY: validate prophet-understand-smoke semantic-enterprise-index-smoke

validate: prophet-understand-smoke semantic-enterprise-index-smoke
	@echo "OK: sherlock-search validate"

prophet-understand-smoke:
	python3 tools/smoke_prophet_understanding_search.py

semantic-enterprise-index-smoke:
	python3 scripts/validate_semantic_enterprise_search_index.py
