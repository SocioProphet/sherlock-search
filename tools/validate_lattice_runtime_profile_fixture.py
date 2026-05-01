#!/usr/bin/env python3
"""Validate Sherlock runtime-profile index fixtures for Lattice Data/GovernAI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "lattice-data-governai" / "runtime-profile-records.sherlock-docs.json"

NOTEBOOK = "runtime-asset:prophet-python-ml:0.1.0"
RAY = "runtime-asset:prophet-ray-ml:0.1.0"
BEAM = "runtime-asset:prophet-beam-dataops:0.1.0"
REQUIRED_RUNTIME_REFS = {NOTEBOOK, RAY, BEAM}
REQUIRED_ASSET_KINDS = {"runtime-asset", "runtime-profile-binding"}
REQUIRED_RUNTIME_CLASSES = {"notebook", "ray", "beam"}
REQUIRED_SOURCE_REFS = {
    "runtimeForgePr",
    "platformRuntimeCatalogPr",
    "agentplaneRuntimeRefsPr",
    "topologyRuntimePr",
}


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
    require(isinstance(value, list) and bool(value), f"{key} must be a non-empty list")
    return value


def validate_doc(doc: dict[str, Any]) -> tuple[str, str | None]:
    require(doc.get("docType") == "lattice.platformAssetRecord", "docType must be lattice.platformAssetRecord")
    require_str(doc, "assetId")
    require_str(doc, "title")
    require_str(doc, "body")
    metadata = doc.get("metadata")
    require(isinstance(metadata, dict), "metadata must be object")
    asset_kind = require_str(metadata, "assetKind")
    require(asset_kind in REQUIRED_ASSET_KINDS, f"unexpected assetKind {asset_kind}")
    require_str(metadata, "sourceKind")
    require_str(metadata, "producerRepo")
    require_str(metadata, "policyRef")
    require_str(metadata, "evidenceCorrelationId")
    surfaces = require_list(metadata, "compatibilitySurfaces")
    require("sherlock-search" in surfaces, "compatibilitySurfaces must include sherlock-search")
    roles = require_list(metadata, "runtimeRoles")
    require(all(isinstance(role, str) and role for role in roles), "runtimeRoles must contain non-empty strings")
    if asset_kind == "runtime-asset":
        runtime_ref = require_str(metadata, "runtimeRef")
        require(runtime_ref in REQUIRED_RUNTIME_REFS, f"unexpected runtimeRef {runtime_ref}")
        runtime_class = require_str(metadata, "runtimeClass")
        require(runtime_class in REQUIRED_RUNTIME_CLASSES, f"unexpected runtimeClass {runtime_class}")
        require(doc["assetId"] == runtime_ref, "runtime assetId must equal runtimeRef")
        return asset_kind, runtime_ref
    runtime_refs = require_list(metadata, "runtimeRefs")
    require(set(runtime_refs) == REQUIRED_RUNTIME_REFS, "runtime-profile-binding must include all runtime refs")
    return asset_kind, None


def main() -> int:
    if not FIXTURE.exists():
        return fail(f"missing {FIXTURE}")
    try:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        require(isinstance(payload, dict), "fixture root must be object")
        require(payload.get("docType") == "lattice.platformAssetRecordSet", "root docType mismatch")
        require_str(payload, "setId")
        source_refs = payload.get("sourceRefs")
        require(isinstance(source_refs, dict), "sourceRefs must be object")
        missing_refs = sorted(REQUIRED_SOURCE_REFS - set(source_refs))
        require(not missing_refs, f"missing sourceRefs: {missing_refs}")
        docs = payload.get("documents")
        require(isinstance(docs, list) and docs, "documents must be non-empty list")
        runtime_refs: set[str] = set()
        asset_kinds: set[str] = set()
        for doc in docs:
            require(isinstance(doc, dict), "documents entries must be objects")
            asset_kind, runtime_ref = validate_doc(doc)
            asset_kinds.add(asset_kind)
            if runtime_ref is not None:
                runtime_refs.add(runtime_ref)
        require(runtime_refs == REQUIRED_RUNTIME_REFS, f"runtime refs mismatch: {sorted(runtime_refs)}")
        require(asset_kinds == REQUIRED_ASSET_KINDS, f"asset kinds mismatch: {sorted(asset_kinds)}")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))
    print(f"PASS {FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
