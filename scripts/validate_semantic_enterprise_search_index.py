#!/usr/bin/env python3
"""Validate Sherlock's Semantic Enterprise v0.1 search-index fixture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/semantic-enterprise/v0.1/search-index.example.json"

REQUIRED_SECTORS = {"finance", "threat-intel", "investigation", "supply-chain", "defense-c2"}
REQUIRED_INDEX_POLICY = {
    "treat_source_as_authoritative",
    "preserve_source_path",
    "preserve_registry_reference",
    "preserve_named_graph_metadata",
    "do_not_promote_examples_to_runtime_truth",
}
REQUIRED_SEARCH_SURFACES = {"module", "scenario", "query", "named_graph", "mapping", "provenance"}
REQUIRED_CLOSURE_FIELDS = {"inside_source", "outside_runtime", "boundary_membrane", "feedback_surface"}


def main() -> int:
    errors: list[str] = []
    if not FIXTURE.is_file():
        print(f"missing fixture: {FIXTURE}")
        return 1

    try:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}")
        return 1

    if data.get("contract") != "sherlock-search.semantic-enterprise.index":
        errors.append("unexpected contract identifier")
    if data.get("version") != "0.1.0":
        errors.append("unexpected contract version")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        expected = {
            "repository": "SocioProphet/ontogenesis",
            "release": "semantic-enterprise-v0.1.0",
            "manifest_path": "manifests/semantic_enterprise_v0_1_manifest.json",
            "rollup_registry_path": "catalog/semantic_enterprise_v0_1_registry.ttl",
        }
        for key, value in expected.items():
            if source.get(key) != value:
                errors.append(f"source.{key} expected {value!r}, got {source.get(key)!r}")

    index_policy = data.get("index_policy")
    if not isinstance(index_policy, dict):
        errors.append("index_policy must be an object")
    else:
        missing = REQUIRED_INDEX_POLICY.difference(index_policy)
        if missing:
            errors.append(f"index_policy missing keys: {sorted(missing)}")
        for key in REQUIRED_INDEX_POLICY.intersection(index_policy):
            if index_policy.get(key) is not True:
                errors.append(f"index_policy.{key} must be true")

    closure = set(data.get("closure_fields") or [])
    if not REQUIRED_CLOSURE_FIELDS.issubset(closure):
        errors.append(f"closure_fields missing: {sorted(REQUIRED_CLOSURE_FIELDS.difference(closure))}")

    surfaces = set(data.get("search_surfaces") or [])
    if not REQUIRED_SEARCH_SURFACES.issubset(surfaces):
        errors.append(f"search_surfaces missing: {sorted(REQUIRED_SEARCH_SURFACES.difference(surfaces))}")

    records = data.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list")
    else:
        sectors = {record.get("sector") for record in records if isinstance(record, dict)}
        if sectors != REQUIRED_SECTORS:
            errors.append(f"expected sectors {sorted(REQUIRED_SECTORS)}, got {sorted(sectors)}")
        ids = set()
        for record in records:
            if not isinstance(record, dict):
                errors.append("record must be an object")
                continue
            record_id = record.get("id")
            if not record_id:
                errors.append("record missing id")
            elif record_id in ids:
                errors.append(f"duplicate record id: {record_id}")
            ids.add(record_id)
            if record.get("kind") != "scenario":
                errors.append(f"record {record_id} kind must be scenario")
            if not str(record.get("source_path", "")).startswith("examples/scenarios/"):
                errors.append(f"record {record_id} source_path must point to examples/scenarios")
            if not str(record.get("query_path", "")).startswith("examples/queries/"):
                errors.append(f"record {record_id} query_path must point to examples/queries")
            if not str(record.get("named_graph_uri_fragment", "")).startswith("graphs/scenarios/"):
                errors.append(f"record {record_id} named graph fragment must point to graphs/scenarios")
            evidence_terms = record.get("evidence_terms")
            if not isinstance(evidence_terms, list) or not evidence_terms:
                errors.append(f"record {record_id} must include evidence_terms")

    if errors:
        print("Semantic Enterprise search-index validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Semantic Enterprise search-index validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
