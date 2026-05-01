#!/usr/bin/env python3
"""Test federated-query-plane record conversion produces the expected query-plane facets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "lattice" / "federated-query-platform-record-set.example.json"
REQUIRED_QUERY_FACETS = {"queryLanguage", "backendKind", "integrationRepo", "catalogScope"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    # Import the converter from the scripts directory.
    sys.path.insert(0, str(ROOT / "scripts"))
    from convert_platform_records import convert_record_set, load_json  # noqa: PLC0415

    doc = load_json(EXAMPLE)
    documents = convert_record_set(doc)

    require(len(documents) >= 1, "expected at least one converted document")

    failed = False
    for idx, document in enumerate(documents):
        label = f"documents[{idx}]"
        try:
            require(document.get("docType") == "lattice.platformAssetRecord", f"{label}: wrong docType")
            metadata = document.get("metadata", {})
            require(metadata.get("sourceKind") == "FederatedQueryPlane", f"{label}: sourceKind must be FederatedQueryPlane")
            for facet in REQUIRED_QUERY_FACETS:
                require(facet in metadata, f"{label}: metadata missing query facet '{facet}'")
                require(metadata[facet], f"{label}: metadata query facet '{facet}' must be non-empty")
            require(metadata.get("policyRef"), f"{label}: policyRef must be present")
            require(metadata.get("evidenceCorrelationId"), f"{label}: evidenceCorrelationId must be present")
            require(isinstance(metadata.get("compatibilitySurfaces"), list), f"{label}: compatibilitySurfaces must be a list")
            print(f"PASS {label} assetId={document.get('assetId')!r} queryLanguage={metadata.get('queryLanguage')!r} backendKind={metadata.get('backendKind')!r}")
        except AssertionError as exc:
            print(f"FAIL {label}: {exc}", file=sys.stderr)
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
