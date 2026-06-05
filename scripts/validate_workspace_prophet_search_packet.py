#!/usr/bin/env python3
"""Validate Workspace PROPHET Sherlock search packet fixture."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "professional-intelligence-search-packet.schema.json"
EXAMPLE = ROOT / "examples" / "workspace-prophet" / "search-packet.example.json"

REQUIRED_EVIDENCE_REFS = {
    "receipt_workspace_diagnostics_completed_demo",
    "op_readonly_diagnostics_demo",
    "cap_local_command_readonly_demo",
    "claim_workspace_readonly_diagnostics_completed_demo",
    "thread_workspace_readonly_diagnostics_completed_demo",
}


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
        print("Workspace PROPHET search packet failed schema validation:")
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

    evidence_refs = set(example.get("evidenceRefs") or [])
    missing = sorted(REQUIRED_EVIDENCE_REFS - evidence_refs)
    if missing:
        print(f"Search packet missing required evidence refs: {missing}")
        return 1

    print("Workspace PROPHET search packet validates against Sherlock schema and evidence requirements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
