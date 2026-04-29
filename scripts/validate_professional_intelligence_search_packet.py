#!/usr/bin/env python3
"""Validate Professional Intelligence search packet example."""

from __future__ import annotations

from pathlib import Path
import json

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "professional-intelligence-search-packet.schema.json"
EXAMPLE = ROOT / "examples" / "professional-intelligence" / "search-packet.example.json"


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
        print("Professional Intelligence search packet failed validation:")
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            print(f" - {location}: {error.message}")
        return 1

    ceiling = example["scope"]["sensitivityCeiling"]
    allowed = ["public", "internal", "confidential", "restricted"]
    ceiling_index = allowed.index(ceiling)
    for result in example["results"]:
        sensitivity = result.get("sensitivity", "public")
        if allowed.index(sensitivity) > ceiling_index:
            print(f"Search result {result['resultId']} exceeds sensitivity ceiling {ceiling}")
            return 1
        if not result.get("citationRefs"):
            print(f"Search result {result['resultId']} lacks citationRefs")
            return 1

    if not example.get("evidenceRefs"):
        print("Search packet requires evidenceRefs")
        return 1

    print("Professional Intelligence search packet validates against schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
