#!/usr/bin/env python3
"""Validate computational artifact search packet example."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "computational-artifact-search-packet.schema.json"
EXAMPLE = ROOT / "examples" / "computational-artifact" / "search-packet.example.json"


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
        print("Computational artifact search packet failed validation:")
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            print(f" - {location}: {error.message}")
        return 1

    allowed_sensitivity = ["public", "internal", "confidential", "restricted"]
    ceiling = example["scope"]["sensitivityCeiling"]
    ceiling_index = allowed_sensitivity.index(ceiling)

    allowed_safety = ["advisory", "bounded", "privileged"]
    safety_ceiling = example["scope"]["safetyCeiling"]
    safety_ceiling_index = allowed_safety.index(safety_ceiling)

    if not example["scope"].get("policyDecisionRefs"):
        print("Computational artifact search packet requires policyDecisionRefs in scope.")
        return 1

    for result in example["results"]:
        if result["artifactRef"] != example["artifactRef"]:
            print(f"Search result {result['resultId']} artifactRef does not match packet artifactRef")
            return 1
        if result["ownerRepo"] != example["ownerRepo"]:
            print(f"Search result {result['resultId']} ownerRepo does not match packet ownerRepo")
            return 1
        if result["runtimeProfile"] != example["runtimeProfile"]:
            print(f"Search result {result['resultId']} runtimeProfile does not match packet runtimeProfile")
            return 1

        sensitivity = result.get("sensitivity", "public")
        if allowed_sensitivity.index(sensitivity) > ceiling_index:
            print(f"Search result {result['resultId']} exceeds sensitivity ceiling {ceiling}")
            return 1

        safety_class = result["safetyClass"]
        if safety_class == "prohibited" or allowed_safety.index(safety_class) > safety_ceiling_index:
            print(f"Search result {result['resultId']} exceeds safety ceiling {safety_ceiling}")
            return 1

    print("Computational artifact search packet validates against schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
