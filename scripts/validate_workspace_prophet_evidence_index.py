#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "workspace-prophet" / "evidence-index.example.json"
REQUIRED_DOCUMENT_TYPES = {
    "workspace_operation",
    "scoped_capability",
    "action_receipt",
    "claim_record",
    "evidence_thread",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "schema_version",
        "index_id",
        "source_repos",
        "operation_id",
        "capability_id",
        "receipt_id",
        "claim_id",
        "evidence_thread_id",
        "lookup_keys",
        "documents",
    ]
    for key in required:
        if key not in packet:
            errors.append(f"missing required key: {key}")

    lookup = packet.get("lookup_keys", {})
    for key in ("operation_id", "capability_id", "receipt_id", "claim_id"):
        if lookup.get(key) != packet.get(key):
            errors.append(f"lookup {key} must match top-level {key}")

    documents = packet.get("documents", [])
    if not documents:
        errors.append("documents must not be empty")

    document_types = {document.get("document_type") for document in documents if isinstance(document, dict)}
    missing_types = sorted(REQUIRED_DOCUMENT_TYPES - document_types)
    if missing_types:
        errors.append(f"missing document types: {missing_types}")

    refs: list[str] = []
    for document in documents:
        if not isinstance(document, dict):
            errors.append("documents must be objects")
            continue
        for key in ("document_id", "document_type", "title", "refs"):
            if key not in document:
                errors.append(f"document missing {key}: {document}")
        refs.extend(document.get("refs", []))

    required_refs = [
        f"operation:{packet.get('operation_id')}",
        f"capability:{packet.get('capability_id')}",
        f"receipt:{packet.get('receipt_id')}",
        f"claim:{packet.get('claim_id')}",
        f"thread:{packet.get('evidence_thread_id')}",
    ]
    for ref in required_refs:
        if ref not in refs:
            errors.append(f"missing searchable ref: {ref}")

    return errors


def main() -> int:
    try:
        packet = load_json(FIXTURE)
    except Exception as exc:
        print(f"ERR: failed to load fixture: {exc}", file=sys.stderr)
        return 2

    errors = validate(packet)
    if errors:
        print("ERR: Workspace PROPHET evidence index validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    print("OK: Workspace PROPHET evidence index fixture passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
