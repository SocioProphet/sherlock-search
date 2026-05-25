.PHONY: validate prophet-understand-smoke semantic-enterprise-index-smoke source-quality-answer-trace-validate citance-claim-candidate-validate

validate: prophet-understand-smoke semantic-enterprise-index-smoke source-quality-answer-trace-validate citance-claim-candidate-validate
	@echo "OK: sherlock-search validate"

prophet-understand-smoke:
	python3 tools/smoke_prophet_understanding_search.py

semantic-enterprise-index-smoke:
	python3 scripts/validate_semantic_enterprise_search_index.py

source-quality-answer-trace-validate:
	python3 tools/validate_source_quality_answer_trace.py

citance-claim-candidate-validate:
	python3 tools/validate_citance_claim_candidate.py
