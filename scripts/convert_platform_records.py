#!/usr/bin/env python3
"""Convert PlatformAssetRecordSet into Sherlock index documents."""

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


def convert_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("kind") != "PlatformAssetRecord":
        raise ValueError("record kind must be PlatformAssetRecord")
    asset_id = _required_str(record, "assetId")
    name = _required_str(record, "name")
    version = _required_str(record, "version")
    asset_kind = _required_str(record, "assetKind")
    producer_repo = _required_str(record, "producerRepo")
    metadata: dict[str, Any] = {
        "assetKind": asset_kind,
        "producerRepo": producer_repo,
        "promotionChannel": record.get("promotionChannel"),
        "compatibilitySurfaces": record.get("compatibilitySurfaces", []),
        "policyRef": record.get("policyRef"),
        "evidenceCorrelationId": record.get("evidenceCorrelationId"),
        "sourceKind": record.get("sourceKind"),
        "sourceApiVersion": record.get("sourceApiVersion"),
    }
    if record.get("sourceKind") == "FederatedQueryPlane":
        for facet in ("queryLanguage", "backendKind", "integrationRepo", "catalogScope"):
            metadata[facet] = record.get(facet)
    return {
        "docType": "lattice.platformAssetRecord",
        "assetId": asset_id,
        "title": f"{name} {version}",
        "body": f"{asset_kind} from {producer_repo} sourceKind={record.get('sourceKind')} promotion={record.get('promotionChannel')}",
        "metadata": metadata,
    }


def convert_record_set(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("kind") != "PlatformAssetRecordSet":
        raise ValueError("kind must be PlatformAssetRecordSet")
    records = doc.get("records")
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    return [convert_record(item) for item in records if isinstance(item, dict)]


def emit_documents(documents: list[dict[str, Any]], output: Path | None) -> None:
    payload = {"documents": documents}
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert PlatformAssetRecordSet to Sherlock index documents")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        emit_documents(convert_record_set(load_json(args.input)), args.output)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"convert_platform_records: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
