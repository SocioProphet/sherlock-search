#!/usr/bin/env python3
"""Print a compact Health AI search packet tranche status summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "registry" / "health-ai-search-packets-proof-2026-06-06.json"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def main() -> None:
    if not PROOF.exists():
        fail(f"missing proof manifest: {PROOF.relative_to(ROOT)}")

    proof = json.loads(PROOF.read_text(encoding="utf-8"))
    if proof.get("repository") != "SocioProphet/sherlock-search":
        fail("repository mismatch")
    if proof.get("tranche") != "health-ai-search-packets-v0":
        fail("tranche mismatch")
    if proof.get("state") != "prototype_only":
        fail("state must be prototype_only")

    results = proof.get("validation_results", {})
    required_passes = [
        "health_ai_search_packets",
        "aggregate_validate",
        "wallguard_retrieval_filter",
        "workspace_prophet_evidence_index",
    ]
    for key in required_passes:
        if results.get(key) != "passed":
            fail(f"validation result {key} must be passed")

    flags = proof.get("status_flags", {})
    for key in [
        "production_ready",
        "clinical_use",
        "patient_specific_guidance",
        "protected_benchmark_disclosure",
        "live_search_deployment",
    ]:
        if flags.get(key) is not False:
            fail(f"status flag {key} must be false")

    wallguard = proof.get("wallguard_examples", {})
    if wallguard.get("cross_wall_rank_exposed") != "rejected":
        fail("cross-wall rank exposed example must remain rejected")
    if wallguard.get("missing_wall_context") != "rejected":
        fail("missing wall context example must remain rejected")
    if wallguard.get("same_wall_pre_rank") != "accepted":
        fail("same-wall pre-rank example must remain accepted")

    print("Health AI Search Packets Status")
    print("===============================")
    print("repository=SocioProphet/sherlock-search")
    print("tranche=health-ai-search-packets-v0")
    print("state=prototype_only")
    print("health_ai_search_packets=passed")
    print("aggregate_validate=passed")
    print("wallguard_cross_wall_rejected=true")
    print("wallguard_missing_context_rejected=true")
    print("wallguard_same_wall_accepted=true")
    print("production_ready=false")
    print("clinical_use=false")
    print("patient_specific_guidance=false")
    print("protected_benchmark_disclosure=false")
    print("live_search_deployment=false")


if __name__ == "__main__":
    main()
