#!/usr/bin/env python3
"""Validate Sherlock replay-evidence fixture for Lattice Data/GovernAI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "lattice-data-governai" / "replay-evidence-bundle.sherlock-docs.json"
RAY = "runtime-asset:prophet-ray-ml:0.1.0"
BEAM = "runtime-asset:prophet-beam-dataops:0.1.0"
REQUIRED_ARTIFACTS = {
    "urn:srcos:artifact:community_truth_demo_ray_metrics",
    "urn:srcos:artifact:community_truth_demo_beam_quality",
    "urn:srcos:model:community_truth_demo_candidate",
}
REQUIRED_RECEIPTS = {
    "urn:srcos:lineage-receipt:ray-community-truth-demo-0001",
    "urn:srcos:lineage-receipt:beam-community-truth-demo-0001",
}
REQUIRED_METRICS = {
    "factuality_f1",
    "grounding_precision",
    "training_records",
    "quality_completeness",
    "annotation_coverage",
    "duplicate_rate",
}
REQUIRED_COMMANDS = {
    "/lattice mlops ray run community_truth_demo --runtime prophet-ray-ml --dry-run",
    "/lattice dataops beam run community_truth_demo --runtime prophet-beam-dataops --dry-run",
}
REQUIRED_SOURCE_REFS = {
    "mlopsReplayEvidencePr",
    "demoReadinessTopologyPr",
    "demoCommandBundlePr",
}


def fail(message: str) -> int:
    print(f"ERR: {message}", file=sys.stderr)
    return 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_list(mapping: dict[str, Any], key: str) -> list[Any]:
    value = mapping.get(key)
    require(isinstance(value, list) and value, f"{key} must be non-empty list")
    return value


def main() -> int:
    if not FIXTURE.exists():
        return fail(f"missing {FIXTURE}")
    try:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        require(payload.get("docType") == "lattice.platformAssetRecordSet", "root docType mismatch")
        source_refs = payload.get("sourceRefs")
        require(isinstance(source_refs, dict), "sourceRefs must be object")
        missing_refs = sorted(REQUIRED_SOURCE_REFS - set(source_refs))
        require(not missing_refs, f"missing sourceRefs: {missing_refs}")
        docs = payload.get("documents")
        require(isinstance(docs, list) and len(docs) == 1, "documents must contain one replay bundle doc")
        doc = docs[0]
        require(doc.get("docType") == "lattice.platformAssetRecord", "doc docType mismatch")
        require(doc.get("assetId") == "urn:srcos:evidence-bundle:lattice-governed-execution-0001", "assetId mismatch")
        metadata = doc.get("metadata")
        require(isinstance(metadata, dict), "metadata must be object")
        require(metadata.get("assetKind") == "replay-evidence-bundle", "assetKind mismatch")
        require(metadata.get("sourceKind") == "ReplayEvidenceBundle", "sourceKind mismatch")
        require(metadata.get("producerRepo") == "SocioProphet/prophet-platform-fabric-mlops-ts-suite", "producerRepo mismatch")
        require(set(require_list(metadata, "runtimeRefs")) == {RAY, BEAM}, "runtimeRefs mismatch")
        require(REQUIRED_ARTIFACTS <= set(require_list(metadata, "artifactRefs")), "artifactRefs incomplete")
        require(REQUIRED_RECEIPTS <= set(require_list(metadata, "lineageReceiptRefs")), "lineageReceiptRefs incomplete")
        require(REQUIRED_METRICS <= set(require_list(metadata, "metricNames")), "metricNames incomplete")
        require(REQUIRED_COMMANDS <= set(require_list(metadata, "replayCommandRefs")), "replayCommandRefs incomplete")
        require(metadata.get("network") == "none", "network must be none")
        require(metadata.get("secrets") == "none", "secrets must be none")
        require(metadata.get("hostMutation") is False, "hostMutation must be false")
        surfaces = set(require_list(metadata, "compatibilitySurfaces"))
        for surface in ["sherlock-search", "slash-topics", "new-hope", "policy-fabric", "agentplane", "cloudshell-fog"]:
            require(surface in surfaces, f"missing surface {surface}")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))
    print(f"PASS {FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
