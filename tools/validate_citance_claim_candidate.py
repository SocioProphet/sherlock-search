#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "citance-claim-candidate.v0.schema.json"
FIXTURES = ROOT / "fixtures" / "citance-claim-candidate"
VALID = FIXTURES / "valid.whitbrock-echoes-citations.unverified.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_semantics(data: dict[str, Any]) -> None:
    boundary = data["boundary"]
    if boundary["candidate_not_truth"] is not True:
        raise ValueError("citance claim candidate must remain candidate_not_truth")
    if data["source_status"] == "unverified_literature_candidate":
        if data["implementation_safe"] is not False:
            raise ValueError("unverified candidate cannot be implementation_safe")
        if data["source_quality"] != "plausible_needs_source":
            raise ValueError("unverified candidate must remain plausible_needs_source")
        if boundary["requires_metadata_verification"] is not True:
            raise ValueError("unverified candidate requires metadata verification")
        if boundary["requires_pdf_verification"] is not True:
            raise ValueError("unverified candidate requires PDF verification")
        if data["claim_candidate"]["claim_status"] != "research_only":
            raise ValueError("unverified candidate claim must remain research_only")


def validate_file(path: Path, schema: dict[str, Any]) -> None:
    data = load_json(path)
    jsonschema.validate(data, schema)
    check_semantics(data)


def main() -> int:
    schema = load_json(SCHEMA)
    validate_file(VALID, schema)
    invalids = sorted(FIXTURES.glob("invalid.*.json"))
    if not invalids:
        raise SystemExit("missing invalid citance claim candidate fixtures")
    passed = []
    for fixture in invalids:
        try:
            validate_file(fixture, schema)
        except Exception:
            continue
        passed.append(fixture.name)
    if passed:
        raise SystemExit("invalid citance fixtures unexpectedly passed: " + ", ".join(passed))
    print("OK: citance claim candidate fixtures validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
