#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "workspace-prophet" / "value-claim-search-packet.example.json"

def main() -> int:
    try:
        packet = json.loads(FIXTURE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERR: failed to load value-claim search packet: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

    if packet.get("schema_version") != "0.1.0":
        errors.append("schema_version must be 0.1.0")
    if packet.get("production_ready") is not False:
        errors.append("production_ready must be false")

    lookup = packet.get("lookup_keys", {})
    for key in ("value_claim_id", "claim_id", "receipt_id", "evidence_thread_id"):
        if lookup.get(key) != packet.get(key):
            errors.append(f"lookup_keys.{key} must match top-level {key}")

    primary = packet.get("value_driver", {}).get("primary")
    if primary != "productivity":
        errors.append("primary value driver must be productivity")
    if lookup.get("primary_value_driver") != primary:
        errors.append("lookup_keys.primary_value_driver must match value_driver.primary")

    facets = packet.get("search_facets", {})
    if facets.get("value_driver") != primary:
        errors.append("search_facets.value_driver must match primary driver")
    if facets.get("production_ready") is not False:
        errors.append("search_facets.production_ready must be false")
    if facets.get("observation_window") != "fixture_validation_only":
        errors.append("observation_window must be fixture_validation_only")
    if facets.get("falsification_required") is not True:
        errors.append("falsification_required must be true")

    refs = packet.get("evidence_refs", [])
    required_fragments = [
        "value-claim-workspace-prophet.json",
        "value-claim-projection-workspace-prophet-v0.json",
        "evidence-index.example.json"
    ]
    for fragment in required_fragments:
        if not any(fragment in ref for ref in refs):
            errors.append(f"missing evidence ref containing {fragment}")

    if errors:
        print("ERR: Workspace PROPHET value-claim search packet validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    print("Workspace PROPHET value-claim search packet validates.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
