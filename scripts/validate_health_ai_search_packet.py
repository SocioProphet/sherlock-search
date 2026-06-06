#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "health-ai-search-packet.schema.json"
FIXTURE = ROOT / "examples" / "health-ai" / "health-ai-search-packet.planning.example.json"

FORBIDDEN_STRINGS = ["healthbench:"]

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    errors: list[str] = []
    try:
        schema = load_json(SCHEMA)
        fixture = load_json(FIXTURE)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(fixture)
    except Exception as exc:
        print(f"ERR: health AI search packet schema validation failed: {exc}", file=sys.stderr)
        return 2

    text = FIXTURE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_STRINGS:
        if forbidden in text:
            errors.append("fixture contains forbidden benchmark leakage marker")

    if fixture.get("readiness_state") != "planning_only":
        errors.append("readiness_state must remain planning_only")
    if fixture.get("production_ready") is not False:
        errors.append("production_ready must be false")
    if fixture.get("patient_care_action") is not False:
        errors.append("patient_care_action must be false")
    if fixture.get("source_claim_class") != "external_competitor_claim":
        errors.append("source_claim_class must be external_competitor_claim for the initial Ambience-derived packet")

    facets = fixture.get("search_facets", {})
    boundary = facets.get("benchmark_boundary", {})
    for key in ("protected_examples_reproduced", "answer_keys_reproduced", "canary_reproduced"):
        if boundary.get(key) is not False:
            errors.append(f"{key} must be false")

    required_blocks = {
        "production_ready",
        "patient_care_action",
        "autonomous_clinical_action",
        "customer_facing_healthcare_claim",
        "benchmark_example_reproduction"
    }
    missing = sorted(required_blocks - set(fixture.get("blocked_from", [])))
    if missing:
        errors.append(f"missing blocked_from entries: {missing}")

    if errors:
        print("ERR: health AI search packet validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    print("Health AI search packet validates.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
