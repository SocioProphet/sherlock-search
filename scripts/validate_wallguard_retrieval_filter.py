#!/usr/bin/env python3
"""Validate WallGuard retrieval-filter examples."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "wallguard-retrieval-filter.schema.json"
EXAMPLE_DIR = ROOT / "examples" / "wallguard-retrieval-filter"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_schema(instance: dict, schema: dict, *, source_label: str) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        lines = [f"{source_label} failed schema validation:"]
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            lines.append(f" - {location}: {error.message}")
        raise ValueError("\n".join(lines))


def semantic_diagnostics(record: dict) -> list[str]:
    diagnostics: list[str] = []
    wall_ref = record["wallRef"]
    outcome = record["wallDecisionOutcome"]
    decision = record["retrievalDecision"]
    resources = record["resources"]

    if record["phase"] != "pre_rank":
        diagnostics.append("WallGuard retrieval filtering must happen at pre_rank phase")

    if wall_ref == "unknown" and decision == "allow":
        diagnostics.append("missing wall context cannot allow retrieval")

    if decision == "allow" and outcome != "allow":
        diagnostics.append("allow retrieval requires WallGuard allow outcome")

    if outcome in {"deny", "quarantine", "clean_room_release_denied"} and decision == "allow":
        diagnostics.append("blocking WallGuard outcome cannot be downgraded to retrieval allow")

    for resource in resources:
        resource_wall = resource["resourceWallRef"]
        visibility = resource["visibility"]
        rank_eligible = resource["rankEligible"]
        same_wall = resource_wall == wall_ref

        if decision == "allow" and not same_wall:
            diagnostics.append(f"cross-wall resource {resource['resourceRef']} cannot be allowed")
        if rank_eligible and not same_wall:
            diagnostics.append(f"cross-wall resource {resource['resourceRef']} cannot be rank eligible")
        if rank_eligible and visibility != "visible":
            diagnostics.append(f"rank-eligible resource {resource['resourceRef']} must be visible")
        if visibility in {"withheld", "quarantined"} and rank_eligible:
            diagnostics.append(f"withheld/quarantined resource {resource['resourceRef']} cannot be rank eligible")

    return diagnostics


def expected_semantic_result(path: Path) -> str:
    return "fail" if ".rejected." in path.name or path.name.startswith("bad-") else "pass"


def main() -> int:
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    examples = sorted(EXAMPLE_DIR.glob("*.example.json"))
    if not examples:
        raise SystemExit("No WallGuard retrieval-filter examples found")

    results = []
    for path in examples:
        record = load_json(path)
        validate_schema(record, schema, source_label=str(path))
        diagnostics = semantic_diagnostics(record)
        actual = "fail" if diagnostics else "pass"
        expected = expected_semantic_result(path)
        results.append({"example": path.name, "expected": expected, "actual": actual, "diagnostics": diagnostics})
        if expected != actual:
            raise ValueError(json.dumps(results[-1], indent=2))

    print(json.dumps({"ok": True, "checked": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
