#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

FAMILY_BOOST = {
    "repo_graph_node": 2.0,
    "repo_graph_edge": 1.8,
    "repo_graph_summary": 1.5,
    "repo_graph_policy": 1.4,
    "repo_graph_validation": 1.2,
    "repo_graph_diff_impact": 1.6,
    "repo_graph_tour": 1.1,
    "repo_graph_receipt": 0.8,
}
RISK_PENALTY = {"deny": -2.0, "require_review": -1.0, "warn": -0.4, "unknown": -0.2, "allow": 0.0}


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def tokens(text: str) -> list[str]:
    return [part for part in re.split(r"[^A-Za-z0-9_.:/-]+", text.lower()) if part]


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        fail(f"missing index: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid index JSON: {exc}")
    if not isinstance(value, list):
        fail("index root must be a list")
    return [item for item in value if isinstance(item, dict)]


def field_text(record: dict[str, Any]) -> str:
    fields = [
        record.get("title", ""),
        record.get("text", ""),
        record.get("record_id", ""),
        record.get("node_id", ""),
        record.get("edge_id", ""),
        record.get("path", ""),
        record.get("record_family", ""),
        record.get("policy_state", ""),
        record.get("validation_status", ""),
    ]
    return " ".join(str(field) for field in fields if field is not None)


def score(record: dict[str, Any], query: str) -> float:
    q_tokens = tokens(query)
    if not q_tokens:
        return 0.0
    text = field_text(record).lower()
    text_tokens = set(tokens(text))
    title = str(record.get("title", "")).lower()
    path = str(record.get("path", "")).lower()
    exact = query.lower() in text
    overlap = sum(1 for token in q_tokens if token in text_tokens)
    partial = sum(1 for token in q_tokens if token in text)
    title_hits = sum(1 for token in q_tokens if token in title)
    path_hits = sum(1 for token in q_tokens if token in path)
    confidence = record.get("confidence")
    confidence_boost = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    family_boost = FAMILY_BOOST.get(record.get("record_family"), 1.0)
    penalty = RISK_PENALTY.get(str(record.get("policy_state", "unknown")), -0.2)
    validation = str(record.get("validation_status", ""))
    validation_penalty = -1.0 if validation in {"invalid", "fail"} else -0.3 if validation in {"warning", "warn"} else 0.0
    return (4.0 if exact else 0.0) + overlap * 2.0 + partial * 0.6 + title_hits * 1.2 + path_hits * 1.0 + math.log1p(family_boost) + confidence_boost + penalty + validation_penalty


def explain(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_family": record.get("record_family"),
        "record_id": record.get("record_id"),
        "title": record.get("title"),
        "path": record.get("path"),
        "node_id": record.get("node_id"),
        "edge_id": record.get("edge_id"),
        "source_anchor": record.get("source_anchor"),
        "confidence": record.get("confidence"),
        "policy_state": record.get("policy_state"),
        "validation_status": record.get("validation_status"),
        "provenance_receipt_ids": record.get("provenance_receipt_ids", []),
        "text": record.get("text"),
    }


def search(records: list[dict[str, Any]], query: str, limit: int) -> dict[str, Any]:
    ranked = []
    for record in records:
        value = score(record, query)
        if value > 0:
            ranked.append((value, record))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].get("record_family", ""), pair[1].get("record_id", "")))
    results = []
    for value, record in ranked[:limit]:
        item = explain(record)
        item["score"] = round(value, 4)
        results.append(item)
    return {
        "query": query,
        "mode": "lexical-graph-evidence-v0",
        "result_count": len(results),
        "results": results,
        "notice": "No semantic/vector certainty is claimed unless upstream records carry embedding evidence.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Lampstand Prophet Understand index records.")
    parser.add_argument("--index", required=True, help="Path to Lampstand repo graph index JSON")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results")
    parser.add_argument("--out", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    records = load_records(Path(args.index))
    result = search(records, args.query, args.limit)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
