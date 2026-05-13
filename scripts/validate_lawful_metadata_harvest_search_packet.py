#!/usr/bin/env python3
"""Validate Sherlock lawful metadata harvest search packet example."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "lawful-metadata-harvest-search-packet.schema.json"
EXAMPLE = ROOT / "examples" / "harvest" / "lawful-metadata-harvest-search-packet.example.json"

SENSITIVITY_ORDER = ["public", "internal", "confidential", "restricted"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    schema = load_json(SCHEMA)
    example = load_json(EXAMPLE)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.path))
    if errors:
        print("Lawful metadata harvest search packet failed schema validation:")
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            print(f" - {location}: {error.message}")
        return 1

    ceiling = example["scope"]["sensitivityCeiling"]
    ceiling_index = SENSITIVITY_ORDER.index(ceiling)

    scope_policy_refs = set(example["scope"].get("policyDecisionRefs", []))
    if not scope_policy_refs:
        print("Search packet requires at least one scope policyDecisionRef")
        return 1

    envelope_ref = example["harvestRun"].get("harvestEnvelopeRef")
    validation_ref = example["harvestRun"].get("validationReportRef")
    if not envelope_ref or not validation_ref:
        print("Harvest run requires harvestEnvelopeRef and validationReportRef")
        return 1

    for result in example["receiptResults"]:
        sensitivity = result.get("sensitivity", "public")
        if SENSITIVITY_ORDER.index(sensitivity) > ceiling_index:
            print(f"Receipt result {result['resultId']} exceeds sensitivity ceiling {ceiling}")
            return 1
        if not result.get("evidenceRefs"):
            print(f"Receipt result {result['resultId']} lacks evidenceRefs")
            return 1
        if not set(result.get("policyDecisionRefs", [])).issubset(scope_policy_refs):
            print(f"Receipt result {result['resultId']} references policy decisions outside packet scope")
            return 1
        if "replayable" not in result.get("handlingTags", []):
            print(f"Receipt result {result['resultId']} must preserve replayable handling tag")
            return 1

    for anomaly in example.get("anomalyResults", []):
        if not anomaly.get("evidenceRefs"):
            print(f"Anomaly {anomaly['anomalyCode']} lacks evidenceRefs")
            return 1

    for decision in example.get("promotionResults", []):
        if decision.get("outcome") == "promoted":
            if not decision.get("validationReportRef"):
                print(f"Promotion {decision['decisionId']} lacks validationReportRef")
                return 1
            if not set(decision.get("policyDecisionRefs", [])).issubset(scope_policy_refs):
                print(f"Promotion {decision['decisionId']} references policy decisions outside packet scope")
                return 1

    evidence_refs = set(example.get("evidenceRefs", []))
    required_refs = {envelope_ref, validation_ref}
    missing = sorted(required_refs.difference(evidence_refs))
    if missing:
        print(f"Search packet evidenceRefs missing required refs: {', '.join(missing)}")
        return 1

    print("Lawful metadata harvest search packet validates against schema and governance checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
