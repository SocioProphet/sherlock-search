#!/usr/bin/env python3
"""Validate Sherlock evidence-answer contract fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TECHNICAL_FIXTURE = ROOT / "fixtures" / "evidence-answer-contract" / "technical-document-answer.sherlock-contract.json"
VECTOR_FIXTURE = ROOT / "fixtures" / "evidence-answer-contract" / "vector-candidate.sherlock-contract.json"


def fail(message: str) -> int:
    print(f"ERR: {message}", file=sys.stderr)
    return 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_non_empty_list(mapping: dict[str, Any], key: str) -> list[Any]:
    value = mapping.get(key)
    require(isinstance(value, list) and value, f"{key} must be a non-empty list")
    return value


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing fixture: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "fixture root must be an object")
    return payload


def validate_technical_fixture() -> None:
    payload = load_json(TECHNICAL_FIXTURE)
    require(payload.get("scenario") == "technical_document_answer", "unexpected technical fixture scenario")
    query = payload.get("query")
    require(isinstance(query, dict) and query.get("text"), "query.text must be present")
    anchors = require_non_empty_list(payload, "anchors")
    anchor_ids = {anchor.get("anchorId") for anchor in anchors if isinstance(anchor, dict)}
    require(None not in anchor_ids, "anchors[].anchorId is required")
    evidence = require_non_empty_list(payload, "evidence")
    evidence_ids = {item.get("evidenceId") for item in evidence if isinstance(item, dict)}
    require(None not in evidence_ids, "evidence[].evidenceId is required")
    for item in evidence:
        require(isinstance(item, dict), "evidence[] item must be object")
        refs = require_non_empty_list(item, "anchorRefs")
        require(set(refs) <= anchor_ids, "evidence.anchorRefs must point to anchors")
    claims = require_non_empty_list(payload, "proposedClaims")
    for claim in claims:
        require(isinstance(claim, dict), "proposedClaims[] item must be object")
        require(claim.get("status") == "proposed", "proposedClaims[].status must be proposed")
        refs = require_non_empty_list(claim, "evidenceRefs")
        require(set(refs) <= evidence_ids, "proposedClaims.evidenceRefs must point to evidence")
    require(isinstance(payload.get("explanationTrace"), dict), "explanationTrace must be object")
    require(isinstance(payload.get("policyDecision"), dict), "policyDecision must be object")


def validate_vector_fixture() -> None:
    payload = load_json(VECTOR_FIXTURE)
    require(payload.get("scenario") == "vector_candidate_only", "unexpected vector fixture scenario")
    query = payload.get("query")
    require(isinstance(query, dict) and query.get("text"), "query.text must be present")
    evidence = require_non_empty_list(payload, "evidence")
    evidence_ids = {item.get("evidenceId") for item in evidence if isinstance(item, dict)}
    require(None not in evidence_ids, "evidence[].evidenceId is required")
    candidates = require_non_empty_list(payload, "vectorCandidates")
    for candidate in candidates:
        require(isinstance(candidate, dict), "vectorCandidates[] item must be object")
        require(candidate.get("status") == "candidate_only", "vectorCandidates[].status must be candidate_only")
        refs = require_non_empty_list(candidate, "evidenceRefs")
        require(set(refs) <= evidence_ids, "vectorCandidates.evidenceRefs must point to evidence")
        metadata = require_non_empty_list(candidate, "roleLevelMatchMetadata")
        for role_match in metadata:
            require(isinstance(role_match, dict), "roleLevelMatchMetadata[] item must be object")
            require(role_match.get("role"), "roleLevelMatchMetadata[].role is required")
            require(role_match.get("queryText"), "roleLevelMatchMetadata[].queryText is required")
            require(role_match.get("matchedText"), "roleLevelMatchMetadata[].matchedText is required")
    require(isinstance(payload.get("explanationTrace"), dict), "explanationTrace must be object")
    require(isinstance(payload.get("policyDecision"), dict), "policyDecision must be object")


def main() -> int:
    try:
        validate_technical_fixture()
        validate_vector_fixture()
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))
    print(f"PASS {TECHNICAL_FIXTURE}")
    print(f"PASS {VECTOR_FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
