#!/usr/bin/env python3
"""Validate Sherlock federated-query-plane fixture.

Dependency-free on purpose: this repo currently acts as a search/discovery
contract surface, so the fixture guard should run anywhere Python is available.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "federated-query" / "federated-query-plane.sherlock-doc.json"
REQUIRED_QUERY_FACETS = {"queryLanguage", "backendKind", "integrationRepo", "catalogScope"}
REQUIRED_SURFACES = {"lattice-studio", "sherlock-search"}
EXPECTED_INTEGRATION_REPO = "SocioProphet/lattice-query-spine"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    metadata = doc.get("metadata", {})
    require(doc.get("docType") == "lattice.platformAssetRecord", "docType must be lattice.platformAssetRecord")
    require(doc.get("assetId", "").startswith("federated-query-plane:"), "assetId must be federated-query-plane:*")
    require(metadata.get("assetKind") == "federated-query-plane", "assetKind must be federated-query-plane")
    require(metadata.get("sourceKind") == "FederatedQueryPlane", "sourceKind must be FederatedQueryPlane")
    require(metadata.get("producerRepo") == "SocioProphet/prophet-platform", "producerRepo must point to prophet-platform")
    require(metadata.get("policyRef"), "policyRef must be present")
    require(metadata.get("evidenceCorrelationId"), "evidenceCorrelationId must be present")
    for facet in REQUIRED_QUERY_FACETS:
        require(facet in metadata and metadata[facet], f"metadata missing required query facet: {facet}")
    require(metadata.get("integrationRepo") == EXPECTED_INTEGRATION_REPO, f"integrationRepo must be {EXPECTED_INTEGRATION_REPO}")
    surfaces = set(metadata.get("compatibilitySurfaces", []))
    require(REQUIRED_SURFACES <= surfaces, f"missing required surfaces: {sorted(REQUIRED_SURFACES - surfaces)}")
    print(f"PASS {FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
