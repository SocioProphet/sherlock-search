#!/usr/bin/env python3
"""Convert PlatformAssetRecordSet into Sherlock index documents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

QUERY_LANGUAGE_BY_SURFACE = {
    "sql": "sql",
    "document-store": "document-query",
    "annotation-store": "annotation-query",
    "sparql": "sparql",
    "ontology-query": "ontology-query",
    "cypher": "cypher",
    "graphbrain": "graphbrain-hypergraph",
    "atomese": "atomese",
    "sherlock-search": "sherlock-query",
    "slash-topics": "slash-topic-query",
    "slash-topics-public-surface": "slash-topic-query",
    "new-hope": "newhope-membrane-query",
    "new-hope-runtime-substrate": "newhope-membrane-query",
    "lampstand": "lampstand-local-query",
}

BACKEND_KIND_BY_SURFACE = {
    "apache-drill": "drill-sql",
    "sql": "drill-sql",
    "document-store": "document-store",
    "annotation-store": "annotation-store",
    "sparql": "rdf-store",
    "ontology-query": "ontology-reasoner",
    "cypher": "property-graph",
    "graphbrain": "hypergraph-store",
    "opencog": "atomspace",
    "atomese": "atomspace",
    "sherlock-search": "sherlock-index",
    "slash-topics": "slash-topic-pack",
    "slash-topics-public-surface": "slash-topic-pack",
    "new-hope": "newhope-runtime",
    "new-hope-runtime-substrate": "newhope-runtime",
    "lampstand": "lampstand-local-index",
}

INTEGRATION_REPO_BY_SURFACE = {
    "sherlock-search": "SocioProphet/sherlock-search",
    "slash-topics": "SocioProphet/slash-topics",
    "slash-topics-public-surface": "SocioProphet/slash-topics",
    "slash-topics-runtime-alias": "SocioProphet/slash-topics",
    "new-hope": "SocioProphet/new-hope",
    "new-hope-runtime-substrate": "SocioProphet/new-hope",
    "new-hope-compatibility": "SocioProphet/new-hope",
    "memory-mesh": "SocioProphet/memory-mesh",
    "lampstand": "SocioProphet/lampstand",
    "ontogenesis": "SocioProphet/ontogenesis",
    "graphbrain": "SocioProphet/graphbrain-contract",
}

QUERY_ROLE_SURFACES = {
    "slash-topics-public-surface",
    "slash-topics-runtime-alias",
    "new-hope-runtime-substrate",
    "new-hope-compatibility",
    "memory-mesh",
}

QUERY_ASSET_KINDS = {"federated-query-plane", "query-routing-dry-run-plan"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def convert_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("kind") != "PlatformAssetRecord":
        raise ValueError("record kind must be PlatformAssetRecord")
    asset_id = _required_str(record, "assetId")
    name = _required_str(record, "name")
    version = _required_str(record, "version")
    asset_kind = _required_str(record, "assetKind")
    producer_repo = _required_str(record, "producerRepo")
    compatibility_surfaces = _string_list(record.get("compatibilitySurfaces", []))
    metadata = {
        "assetKind": asset_kind,
        "producerRepo": producer_repo,
        "promotionChannel": record.get("promotionChannel"),
        "compatibilitySurfaces": compatibility_surfaces,
        "policyRef": record.get("policyRef"),
        "evidenceCorrelationId": record.get("evidenceCorrelationId"),
        "sourceKind": record.get("sourceKind"),
        "sourceApiVersion": record.get("sourceApiVersion"),
    }
    query_facets = query_facets_for_record(record, compatibility_surfaces)
    if query_facets is not None:
        metadata["queryFacets"] = query_facets
    return {
        "docType": "lattice.platformAssetRecord",
        "assetId": asset_id,
        "title": f"{name} {version}",
        "body": body_for_record(record, query_facets),
        "metadata": metadata,
    }


def body_for_record(record: dict[str, Any], query_facets: dict[str, Any] | None) -> str:
    asset_kind = _required_str(record, "assetKind")
    producer_repo = _required_str(record, "producerRepo")
    base = f"{asset_kind} from {producer_repo} sourceKind={record.get('sourceKind')} promotion={record.get('promotionChannel')}"
    if not query_facets:
        return base
    languages = ",".join(query_facets.get("queryLanguages", []))
    backends = ",".join(query_facets.get("backendKinds", []))
    roles = ",".join(query_facets.get("queryEnvelopeRoles", []))
    return f"{base} queryLanguages={languages} backendKinds={backends} queryEnvelopeRoles={roles}"


def query_facets_for_record(record: dict[str, Any], compatibility_surfaces: list[str]) -> dict[str, Any] | None:
    asset_kind = record.get("assetKind")
    if asset_kind not in QUERY_ASSET_KINDS:
        return None
    surfaces = set(compatibility_surfaces)
    query_languages = sorted({language for surface, language in QUERY_LANGUAGE_BY_SURFACE.items() if surface in surfaces})
    backend_kinds = sorted({kind for surface, kind in BACKEND_KIND_BY_SURFACE.items() if surface in surfaces})
    integration_repos = sorted({repo for surface, repo in INTEGRATION_REPO_BY_SURFACE.items() if surface in surfaces})
    role_surfaces = sorted(surface for surface in QUERY_ROLE_SURFACES if surface in surfaces)
    return {
        "facetSchema": "sherlock.lattice.query.facets/v1",
        "queryLanguages": query_languages,
        "backendKinds": backend_kinds,
        "integrationRepos": integration_repos,
        "queryEnvelopeRoles": role_surfaces,
        "policyRef": record.get("policyRef"),
        "evidenceCorrelationId": record.get("evidenceCorrelationId"),
        "catalogScopes": [],
        "catalogScopeSource": "not-present-in-platform-record",
    }


def convert_record_set(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("kind") != "PlatformAssetRecordSet":
        raise ValueError("kind must be PlatformAssetRecordSet")
    records = doc.get("records")
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    return [convert_record(item) for item in records if isinstance(item, dict)]


def emit_documents(documents: list[dict[str, Any]], output: Path | None) -> None:
    payload = {"documents": documents}
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert PlatformAssetRecordSet to Sherlock index documents")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        emit_documents(convert_record_set(load_json(args.input)), args.output)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"convert_platform_records: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
