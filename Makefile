.PHONY: validate prophet-understand-smoke semantic-enterprise-index-smoke source-quality-answer-trace-validate citance-claim-candidate-validate validate-wallguard-retrieval-filter

validate: prophet-understand-smoke semantic-enterprise-index-smoke source-quality-answer-trace-validate citance-claim-candidate-validate validate-wallguard-retrieval-filter
	@echo "OK: sherlock-search validate"

prophet-understand-smoke:
	python3 tools/smoke_prophet_understanding_search.py

semantic-enterprise-index-smoke:
	python3 scripts/validate_semantic_enterprise_search_index.py

source-quality-answer-trace-validate:
	python3 tools/validate_source_quality_answer_trace.py

citance-claim-candidate-validate:
	python3 tools/validate_citance_claim_candidate.py

validate-wallguard-retrieval-filter:
	python3 scripts/validate_wallguard_retrieval_filter.py
