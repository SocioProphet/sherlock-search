#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_SCHEMA = ROOT / "schemas" / "health-ai-search-packet.schema.json"
LEGACY_EXAMPLES = [
    ROOT / "examples" / "health-ai" / "clinical-value-source-search-packet.example.json",
    ROOT / "examples" / "health-ai" / "health-eval-design-search-packet.example.json",
]
V0_SCHEMA = ROOT / "schemas" / "health-ai-search-packet-v0.schema.json"
V0_VALID = ROOT / "examples" / "health-ai" / "health-ai-search-packet.valid.json"
V0_INVALID = ROOT / "examples" / "health-ai" / "health-ai-search-packet.invalid.synthetic.json"

LEGACY_REQUIRED = {
    "schema_version", "packet_id", "source_class", "readiness_state", "production_ready",
    "patient_care_action", "customer_facing_claim", "source_material", "lookup_keys",
    "evidence_refs", "facets", "summary",
}
V0_REQUIRED = {
    "schema_version", "packet_id", "domain", "intent", "query_text", "safety_profile",
    "retrieval_policy", "privacy_controls", "output_policy", "status",
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_legacy(packet: dict) -> list[str]:
    errors: list[str] = []
    if set(packet) != LEGACY_REQUIRED:
        errors.append("legacy_fields")
    if packet.get("schema_version") != "0.1.0":
        errors.append("legacy_version")
    for key in ["production_ready", "patient_care_action", "customer_facing_claim"]:
        if packet.get(key) is not False:
            errors.append(key)
    boundary = packet.get("facets", {}).get("benchmark_boundary", {})
    for key in ["protected_examples_reproduced", "answer_keys_reproduced", "canary_reproduced"]:
        if boundary.get(key) is not False:
            errors.append(key)
    if packet.get("source_class") == "external_competitor_claim" and "ambience_healthcare" not in packet.get("source_material", []):
        errors.append("source_material")
    if packet.get("source_class") == "benchmark_design_claim" and "healthbench_openai" not in packet.get("source_material", []):
        errors.append("source_material")
    if "healthbench:" in json.dumps(packet):
        errors.append("forbidden_marker")
    return errors


def check_v0(packet: dict) -> list[str]:
    errors: list[str] = []
    if set(packet) != V0_REQUIRED:
        errors.append("v0_fields")
    if packet.get("schema_version") != "v0":
        errors.append("v0_version")
    if packet.get("domain") != "health_ai":
        errors.append("domain")
    if packet.get("status") != "prototype_only":
        errors.append("status")
    safety = packet.get("safety_profile", {})
    if safety.get("scope") != "informational_search_only":
        errors.append("scope")
    for key in ["personal_action_recommendation_requested", "urgent_decision_support_requested"]:
        if safety.get(key) is not False:
            errors.append(key)
    if safety.get("human_expert_boundary_required") is not True:
        errors.append("boundary")
    retrieval = packet.get("retrieval_policy", {})
    if len(retrieval.get("allowed_source_classes", [])) < 3:
        errors.append("sources")
    for key in ["recency_check_required", "citation_required"]:
        if retrieval.get(key) is not True:
            errors.append(key)
    privacy = packet.get("privacy_controls", {})
    if privacy.get("personal_identifiers_included") is not False:
        errors.append("identifiers")
    if privacy.get("free_text_identifier_screen_required") is not True:
        errors.append("identifier_screen")
    output = packet.get("output_policy", {})
    if output.get("personal_instruction_output_allowed") is not False:
        errors.append("instruction_output")
    if output.get("human_expert_boundary_notice_required") is not True:
        errors.append("notice")
    return errors


def main() -> int:
    errors: list[str] = []
    legacy_schema = read(LEGACY_SCHEMA)
    v0_schema = read(V0_SCHEMA)
    if set(legacy_schema.get("required", [])) != LEGACY_REQUIRED:
        errors.append("legacy_schema_required")
    if set(v0_schema.get("required", [])) != V0_REQUIRED:
        errors.append("v0_schema_required")

    for path in LEGACY_EXAMPLES:
        packet_errors = check_legacy(read(path))
        errors.extend(f"{path.relative_to(ROOT)}:{err}" for err in packet_errors)

    valid_errors = check_v0(read(V0_VALID))
    errors.extend(f"{V0_VALID.relative_to(ROOT)}:{err}" for err in valid_errors)
    invalid_errors = check_v0(read(V0_INVALID))
    if not invalid_errors:
        errors.append("invalid_fixture_unexpectedly_passed")

    if errors:
        print("FAIL: Health AI search packet validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("PASS: Health AI search packets validate")
    print("legacy_schema=schemas/health-ai-search-packet.schema.json")
    print("v0_schema=schemas/health-ai-search-packet-v0.schema.json")
    print("legacy_examples=2")
    print("v0_valid_examples=1")
    print("v0_invalid_examples=1")
    print(f"v0_invalid_fixture_errors={len(invalid_errors)}")
    print("production_ready=false")
    print("status=prototype_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
