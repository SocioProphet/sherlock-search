#!/usr/bin/env python3
"""Validate Sherlock source-quality answer trace fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required: python -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "source-quality-answer-trace.v0.schema.json"
FIXTURE_DIR = ROOT / "fixtures" / "source-quality-answer-trace"
VALID = FIXTURE_DIR / "valid.confirmed-bibliographic.json"
INVALID_DIR = FIXTURE_DIR
IMPLEMENTATION_SAFE_QUALITIES = {
    "confirmed_official",
    "confirmed_bibliographic",
    "confirmed_pdf",
    "confirmed_artifact",
}
RESEARCH_ONLY_QUALITIES = {
    "plausible_needs_source",
    "speculative_do_not_use",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be object")
    return data


def semantic_check(data: dict[str, Any]) -> None:
    sources = {src["source_id"]: src for src in data.get("sources", [])}
    claims = {claim["claim_id"]: claim for claim in data.get("claims", [])}
    findings = {finding["finding_id"]: finding for finding in data.get("diagnostic_findings", [])}

    if not sources:
        raise ValueError("sources must not be empty")
    if not claims:
        raise ValueError("claims must not be empty")

    for claim in claims.values():
        for ref in claim.get("evidence_refs", []):
            if ref not in sources:
                raise ValueError(f"claim {claim['claim_id']} references unknown evidence {ref}")

    for finding in findings.values():
        for ref in finding.get("evidence_refs", []):
            if ref not in sources:
                raise ValueError(f"finding {finding['finding_id']} references unknown evidence {ref}")

    trace = data.get("answer_trace", {})
    for ref in trace.get("claim_refs", []):
        if ref not in claims:
            raise ValueError(f"answer_trace references unknown claim {ref}")
    for ref in trace.get("evidence_refs", []):
        if ref not in sources:
            raise ValueError(f"answer_trace references unknown evidence {ref}")
    for ref in trace.get("diagnostic_refs", []):
        if ref not in findings:
            raise ValueError(f"answer_trace references unknown diagnostic finding {ref}")

    trace_qualities = {sources[ref]["source_quality"] for ref in trace.get("evidence_refs", [])}
    if trace.get("implementation_safe") or trace.get("evidence_grade") == "implementation_safe":
        if trace_qualities & RESEARCH_ONLY_QUALITIES:
            raise ValueError("research-only source quality cannot produce an implementation-safe answer trace")
        if not trace_qualities <= IMPLEMENTATION_SAFE_QUALITIES:
            raise ValueError("implementation-safe answer trace requires confirmed source qualities")

    if any(claim.get("claim_status") == "research_only" for claim in claims.values()):
        if trace.get("implementation_safe"):
            raise ValueError("research-only claims cannot be marked implementation_safe")


def validate_fixture(path: Path, schema: dict[str, Any]) -> None:
    data = load_json(path)
    jsonschema.validate(data, schema)
    semantic_check(data)


def main() -> int:
    schema = load_json(SCHEMA)
    validate_fixture(VALID, schema)

    invalid_fixtures = sorted(FIXTURE_DIR.glob("invalid.*.json"))
    if not invalid_fixtures:
        raise SystemExit("missing invalid source-quality answer trace fixtures")

    unexpected_pass = []
    for fixture in invalid_fixtures:
        try:
            validate_fixture(fixture, schema)
        except Exception:
            continue
        unexpected_pass.append(str(fixture.relative_to(ROOT)))

    if unexpected_pass:
        raise SystemExit("invalid fixtures unexpectedly passed: " + ", ".join(unexpected_pass))

    print("OK: source-quality answer trace fixtures validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
