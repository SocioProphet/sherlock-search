#!/usr/bin/env python3
"""Validate expanded Sherlock Lattice Data/GovernAI index fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "lattice-data-governai" / "expanded-platform-asset-records.sherlock-docs.json"

REQUIRED_ASSET_KINDS = {
    "model-zoo-entry",
    "model-endpoint",
    "prompt-asset",
    "rag-pipeline",
    "vector-index",
    "research-package",
    "training-dataset",
    "evaluation-dataset",
    "annotation-reliability-score",
    "trust-posture-summary",
    "trust-signal",
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


def fail(message: str) -> int:
    print(f"ERR: {message}", file=sys.stderr)
    return 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_str(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    require(isinstance(value, str) and bool(value), f"{key} must be non-empty string")
    return value


def require_list(mapping: dict[str, Any], key: str) -> list[Any]:
    value = mapping.get(key)
    require(isinstance(value, list) and bool(value), f"{key} must be non-empty list")
    return value


def validate_doc(doc: dict[str, Any]) -> str:
    require(doc.get("docType") == "lattice.platformAssetRecord", "docType must be lattice.platformAssetRecord")
    require_str(doc, "assetId")
    require_str(doc, "title")
    require_str(doc, "body")
    metadata = doc.get("metadata")
    require(isinstance(metadata, dict), "metadata must be object")
    missing = sorted(REQUIRED_METADATA - set(metadata))
    require(not missing, f"metadata missing {missing}")
    asset_kind = require_str(metadata, "assetKind")
    require(asset_kind in REQUIRED_ASSET_KINDS, f"unexpected assetKind {asset_kind}")
    require(metadata.get("producerRepo") == "SocioProphet/prophet-platform", "producerRepo must be prophet-platform")
    require(metadata.get("promotionChannel") == "lattice-data-governai-demo", "promotionChannel mismatch")
    require(metadata.get("runtimeRef") == "runtime-asset:prophet-python-ml:0.1.0", "runtimeRef mismatch")
    surfaces = require_list(metadata, "compatibilitySurfaces")
    require("sherlock-search" in surfaces, f"{asset_kind} must include sherlock-search surface")
    lineage = metadata.get("dataLineageRefs", [])
    require(isinstance(lineage, list), "dataLineageRefs must be a list when present")
    if asset_kind in {"model-zoo-entry", "prompt-asset", "rag-pipeline", "research-package", "training-dataset", "evaluation-dataset", "trust-posture-summary"}:
        require("urn:srcos:data-product:community_truth_demo" in lineage, f"{asset_kind} must preserve DataProduct lineage")
    trust = metadata.get("trustScore")
    if trust is not None:
        require(isinstance(trust, (int, float)) and 0 <= trust <= 1, "trustScore must be in [0, 1]")
    return asset_kind


def main() -> int:
    if not FIXTURE.exists():
        return fail(f"missing {FIXTURE}")
    try:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        require(isinstance(payload, dict), "fixture root must be object")
        require(payload.get("docType") == "lattice.platformAssetRecordSet", "root docType mismatch")
        require_str(payload, "setId")
        docs = payload.get("documents")
        require(isinstance(docs, list) and docs, "documents must be non-empty list")
        kinds = {validate_doc(doc) for doc in docs if isinstance(doc, dict)}
        missing = sorted(REQUIRED_ASSET_KINDS - kinds)
        require(not missing, f"missing asset kinds: {missing}")
        source_refs = payload.get("sourceRefs")
        require(isinstance(source_refs, dict), "sourceRefs must be object")
        for key in ["modelZooPr", "promptRagEvalPr", "publicationReviewPr", "annotationTrainingPr", "activeMetadataPr", "trustReputationPr"]:
            require_str(source_refs, key)
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))
    print(f"PASS {FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
