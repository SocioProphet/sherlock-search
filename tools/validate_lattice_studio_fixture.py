#!/usr/bin/env python3
"""Validate Lattice Studio workspace Sherlock fixture.

Dependency-free on purpose: this repo currently acts as a search/discovery
contract surface, so the fixture guard should run anywhere Python is available.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "lattice-studio" / "workspace-synthesis.sherlock-doc.json"
REQUIRED_TOPICS = {
    "/lattice/studio",
    "/workspace/synthesis",
    "/source-grounded-synthesis",
    "/workspace/publication",
    "/evidence",
    "/governance",
}
REQUIRED_SURFACES = {
    "lattice-studio",
    "prophet-workspace",
    "prophet-platform",
    "source-grounded-synthesis",
    "workspace-publication",
    "evidence-bundle",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    metadata = doc.get("metadata", {})
    require(doc.get("docType") == "lattice.platformAssetRecord", "docType must be lattice.platformAssetRecord")
    require(doc.get("assetId", "").startswith("workspace-synthesis:"), "assetId must be workspace-synthesis:*" )
    require(metadata.get("assetKind") == "workspace-synthesis-artifact", "assetKind must be workspace-synthesis-artifact")
    require(metadata.get("producerRepo") == "SocioProphet/prophet-platform", "producerRepo must point to prophet-platform")
    require(metadata.get("policyRef"), "policyRef must be present")
    require(metadata.get("evidenceCorrelationId"), "evidenceCorrelationId must be present")
    topics = set(metadata.get("slashTopics", []))
    surfaces = set(metadata.get("compatibilitySurfaces", []))
    require(REQUIRED_TOPICS <= topics, f"missing required topics: {sorted(REQUIRED_TOPICS - topics)}")
    require(REQUIRED_SURFACES <= surfaces, f"missing required surfaces: {sorted(REQUIRED_SURFACES - surfaces)}")
    governance = metadata.get("governance", {})
    require(governance.get("evidenceCompleteness") == "policy-and-evidence-linked", "evidence completeness must be policy-and-evidence-linked")
    require(governance.get("searchVisibility") == "policy-scoped", "search visibility must be policy-scoped")
    print(f"PASS {FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
