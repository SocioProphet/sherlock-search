#!/usr/bin/env python3
"""Validate Sherlock Lattice Data/GovernAI index fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "lattice-data-governai" / "platform-asset-records.sherlock-docs.json"

REQUIRED_ASSET_KINDS = {
    "data-product",
    "runtime-asset",
    "query-run",
    "evaluation-bundle",
    "factsheet",
    "publication-artifact",
    "ray-job-dry-run",
    "beam-pipeline-dry-run",
}
REQUIRED_METADATA = {
    "assetKind",
    "sourceKind",
    "producerRepo",
    "sourceApiVersion",
    "policyRef",
    "evidenceCorrelationId",
    "promotionChannel",
    "runtimeRef",
    "evaluationStatus",
    "publicationStatus",
    "compatibilitySurfaces",
}
REQUIRED_SURFACE = "sherlock-search"


def fail(message: str) -> int:
    print(f"ERR: {message}", file=sys.stderr)
    return 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_str(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    require(isinstance(value, str) and bool(value), f"{key} must be a non-empty string")
    return value


def require_list(mapping: dict[str, Any], key: str) -> list[Any]:
    value = mapping.get(key)
    require(isinstance(value, list), f"{key} must be a list")
    require(bool(value), f"{key} must not be empty")
    return value


def validate_document(doc: dict[str, Any]) -> str:
    require(doc.get("docType") == "lattice.platformAssetRecord", "docType must be lattice.platformAssetRecord")
    require_str(doc, "assetId")
    require_str(doc, "title")
    require_str(doc, "body")
    metadata = doc.get("metadata")
    require(isinstance(metadata, dict), "metadata must be object")
    missing = sorted(REQUIRED_METADATA - set(metadata))
    require(not missing, f"metadata missing required keys: {missing}")
    asset_kind = require_str(metadata, "assetKind")
    require(asset_kind in REQUIRED_ASSET_KINDS, f"unexpected assetKind: {asset_kind}")
    require_str(metadata, "sourceKind")
    require_str(metadata, "producerRepo")
    require_str(metadata, "sourceApiVersion")
    require_str(metadata, "policyRef")
    require_str(metadata, "evidenceCorrelationId")
    require(metadata.get("promotionChannel") == "lattice-data-governai-demo" or asset_kind == "runtime-asset", "promotionChannel must be lattice-data-governai-demo except runtime dev artifact")
    surfaces = require_list(metadata, "compatibilitySurfaces")
    require(REQUIRED_SURFACE in surfaces, f"compatibilitySurfaces must include {REQUIRED_SURFACE}")
    require(metadata.get("runtimeRef") == "runtime-asset:prophet-python-ml:0.1.0", "runtimeRef must preserve RuntimeAsset identity")
    if asset_kind in {"data-product", "query-run", "evaluation-bundle", "factsheet", "publication-artifact", "ray-job-dry-run", "beam-pipeline-dry-run"}:
        lineage = metadata.get("dataLineageRefs", [])
        require(isinstance(lineage, list), "dataLineageRefs must be list when present")
        require("urn:srcos:data-product:community_truth_demo" in lineage or asset_kind == "data-product", f"{asset_kind} must preserve DataProduct lineage")
    return asset_kind


def main() -> int:
    if not FIXTURE.exists():
        return fail(f"missing {FIXTURE}")
    try:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        require(isinstance(payload, dict), "fixture root must be object")
        require(payload.get("docType") == "lattice.platformAssetRecordSet", "root docType must be lattice.platformAssetRecordSet")
        require_str(payload, "setId")
        docs = payload.get("documents")
        require(isinstance(docs, list) and docs, "documents must be non-empty list")
        asset_kinds = {validate_document(doc) for doc in docs if isinstance(doc, dict)}
        missing_kinds = sorted(REQUIRED_ASSET_KINDS - asset_kinds)
        require(not missing_kinds, f"missing asset kinds: {missing_kinds}")
        require(len(asset_kinds) == len(docs), "documents must have unique asset kinds in this fixture")
        source_refs = payload.get("sourceRefs")
        require(isinstance(source_refs, dict), "sourceRefs must be object")
        for key in ["schemaPr", "platformPr", "runtimePr", "mlopsPr", "policyPr", "topologyPr"]:
            require_str(source_refs, key)
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))
    print(f"PASS {FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
