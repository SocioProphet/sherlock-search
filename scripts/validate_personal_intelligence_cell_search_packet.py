#!/usr/bin/env python3
"""Validate Personal Intelligence Cell search packet example."""

from __future__ import annotations

from pathlib import Path
import json

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover
    Draft202012Validator = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "professional-intelligence-search-packet.schema.json"
EXAMPLE = ROOT / "examples" / "personal-intelligence-cell" / "search-packet.example.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> int:
    print(f"Personal Intelligence Cell search packet failed validation: {message}")
    return 1


def main() -> int:
    schema = load_json(SCHEMA)
    example = load_json(EXAMPLE)

    if Draft202012Validator is not None:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(example), key=lambda error: list(error.path))
        if errors:
            for error in errors:
                location = ".".join(str(part) for part in error.path) or "<root>"
                print(f" - {location}: {error.message}")
            return 1

    if example.get("schemaVersion") != "v0.1":
        return fail("schemaVersion must be v0.1")
    if not example.get("searchPacketId", "").startswith("search-packet://cell/"):
        return fail("searchPacketId must be cell-scoped")
    if not example.get("workroomRef", "").startswith("workroom://cell/"):
        return fail("workroomRef must be cell-scoped")
    if example.get("playbookId") != "playbook://personal-intelligence-cell/watch-signal":
        return fail("playbookId mismatch")
    if not example.get("scope", {}).get("policyDecisionRefs"):
        return fail("scope.policyDecisionRefs required")
    if not example.get("evidenceRefs"):
        return fail("evidenceRefs required")
    results = example.get("results", [])
    if len(results) != 1:
        return fail("exactly one seed result required")
    result = results[0]
    if not result.get("citationRefs"):
        return fail("result citationRefs required")
    if result.get("evidenceRef") not in result.get("citationRefs", []):
        return fail("result evidenceRef must be included in citationRefs")
    if result.get("confidence", 0) <= 0:
        return fail("result confidence must be positive")
    allowed = ["public", "internal", "confidential", "restricted"]
    ceiling = example["scope"]["sensitivityCeiling"]
    if allowed.index(result.get("sensitivity", "public")) > allowed.index(ceiling):
        return fail("result sensitivity exceeds scope ceiling")

    print("Personal Intelligence Cell search packet validates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
