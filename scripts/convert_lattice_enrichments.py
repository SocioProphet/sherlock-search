#!/usr/bin/env python3
"""Convert PlatformAssetRecordEnrichmentSet into Sherlock index documents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def convert_enrichment(enrichment: dict[str, Any]) -> dict[str, Any]:
    asset_id = _required_str(enrichment, "assetId")
    search = _required_dict(enrichment, "search")
    facets = _required_dict(search, "facets")
    return {
        "docType": "lattice.platformAssetRecord",
        "assetId": asset_id,
        "title": _required_str(search, "title"),
        "body": enrichment.get("languageModeling", {}).get("plainLanguageSummary", ""),
        "metadata": {
            "assetKind": facets.get("assetKind"),
            "producerRepo": facets.get("producerRepo"),
            "promotionChannel": facets.get("promotionChannel"),
            "compatibilitySurfaces": facets.get("compatibilitySurfaces", []),
            "slashTopics": enrichment.get("slashTopics", []),
            "policySubjectClass": enrichment.get("policyFabric", {}).get("subjectClass"),
            "contractSubjectClass": enrichment.get("contractForge", {}).get("subjectClass"),
            "languageModelingUse": enrichment.get("languageModeling", {}).get("use"),
        },
    }


def convert_enrichment_set(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("kind") != "PlatformAssetRecordEnrichmentSet":
        raise ValueError("kind must be PlatformAssetRecordEnrichmentSet")
    enrichments = doc.get("enrichments")
    if not isinstance(enrichments, list):
        raise ValueError("enrichments must be a list")
    return [convert_enrichment(item) for item in enrichments if isinstance(item, dict)]


def emit_documents(documents: list[dict[str, Any]], output: Path | None) -> None:
    payload = {"documents": documents}
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def _required_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert Lattice enrichment set to Sherlock index documents")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        documents = convert_enrichment_set(load_json(args.input))
        emit_documents(documents, args.output)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"convert_lattice_enrichments: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
