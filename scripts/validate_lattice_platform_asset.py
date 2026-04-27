#!/usr/bin/env python3
"""Validate Sherlock Lattice platform asset index fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


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
