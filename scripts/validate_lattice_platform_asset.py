#!/usr/bin/env python3
"""Validate Sherlock Lattice platform asset index fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

QUERY_ASSET_KINDS = {"federated-query-plane", "query-routing-dry-run-plan"}
REQUIRED_QUERY_FACET_KEYS = {
    "facetSchema",
    "queryLanguages",
    "backendKinds",
    "integrationRepos",
    "queryEnvelopeRoles",
    "policyRef",
    "evidenceCorrelationId",
    "catalogScopes",
    "catalogScopeSource",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_document(doc: dict[str, Any]) -> None:
    require(doc.get("docType") == "lattice.platformAssetRecord", "docType must be lattice.platformAssetRecord")
    for key in ["assetId", "title", "body", "metadata"]:
        require(key in doc, f"missing {key}")
    metadata = doc["metadata"]
    require(isinstance(metadata, dict), "metadata must be an object")
    for key in ["assetKind", "producerRepo", "compatibilitySurfaces"]:
        require(key in metadata, f"metadata missing {key}")
    require(isinstance(metadata["compatibilitySurfaces"], list), "compatibilitySurfaces must be a list")
    if metadata.get("assetKind") in QUERY_ASSET_KINDS:
        validate_query_facets(metadata)


def validate_query_facets(metadata: dict[str, Any]) -> None:
    facets = metadata.get("queryFacets")
    require(isinstance(facets, dict), "query platform asset metadata must include queryFacets")
    missing = sorted(REQUIRED_QUERY_FACET_KEYS - set(facets))
    require(not missing, f"queryFacets missing keys: {missing}")
    require(facets.get("facetSchema") == "sherlock.lattice.query.facets/v1", "queryFacets facetSchema mismatch")
    for key in ["queryLanguages", "backendKinds", "integrationRepos", "queryEnvelopeRoles", "catalogScopes"]:
        require(isinstance(facets.get(key), list), f"queryFacets.{key} must be a list")
    require(isinstance(facets.get("policyRef"), str) and facets["policyRef"], "queryFacets.policyRef must be a non-empty string")
    require(isinstance(facets.get("evidenceCorrelationId"), str) and facets["evidenceCorrelationId"], "queryFacets.evidenceCorrelationId must be a non-empty string")
    require(isinstance(facets.get("catalogScopeSource"), str) and facets["catalogScopeSource"], "queryFacets.catalogScopeSource must be a non-empty string")
    require(facets["queryLanguages"], "queryFacets.queryLanguages must not be empty")
    require(facets["backendKinds"], "queryFacets.backendKinds must not be empty")
    require(facets["integrationRepos"], "queryFacets.integrationRepos must not be empty")
    if metadata.get("assetKind") == "query-routing-dry-run-plan":
        role_surfaces = set(facets["queryEnvelopeRoles"])
        for required in [
            "slash-topics-public-surface",
            "slash-topics-runtime-alias",
            "new-hope-runtime-substrate",
            "new-hope-compatibility",
            "memory-mesh",
        ]:
            require(required in role_surfaces, f"query-routing queryFacets missing envelope role {required}")


def validate(path: Path) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(doc, dict) and "documents" in doc:
        documents = doc["documents"]
        require(isinstance(documents, list) and documents, "documents must be a non-empty list")
        for index, item in enumerate(documents):
            require(isinstance(item, dict), f"documents[{index}] must be an object")
            validate_document(item)
        return
    require(isinstance(doc, dict), "fixture must be an object")
    validate_document(doc)


def main(argv: list[str] | None = None) -> int:
    paths = [Path(arg) for arg in (argv if argv is not None else sys.argv[1:])]
    if not paths:
        paths = sorted(Path("examples/lattice").glob("platform-asset-index-document*.json"))
    failed = False
    for path in paths:
        try:
            validate(path)
            print(f"PASS {path}")
        except Exception as exc:  # noqa: BLE001
            failed = True
            print(f"FAIL {path}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
