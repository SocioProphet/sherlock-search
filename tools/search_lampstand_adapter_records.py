#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

KIND_BOOST = {
    "repo_context": 2.0,
    "repo_structure": 1.8,
    "security_signal": 1.7,
    "memory_candidate": 1.4,
    "symbol": 1.6,
}
RECORD_TYPE_BOOST = {
    "sourceos.lampstand.repo_context_record.v1": 2.0,
    "sourceos.lampstand.repo_structure_record.v1": 1.8,
    "sourceos.lampstand.security_search_record.v1": 1.7,
    "sourceos.lampstand.memory_candidate_record.v1": 1.4,
}
POLICY_PENALTY = {
    "deny": -3.0,
    "review_required": -1.2,
    "allow_with_redaction": -0.4,
    "allow": 0.0,
    "unknown": -0.2,
}


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def tokens(text: str) -> list[str]:
    return [part for part in re.split(r"[^A-Za-z0-9_.:/-]+", text.lower()) if part]


def load_payload(path: Path) -> Any:
    if not path.exists():
        fail(f"missing index: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid adapter-record JSON: {exc}")


def extract_records(value: Any) -> list[dict[str, Any]]:
    """Accept raw record lists and common Lampstand/Sherlock envelopes."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("records", "hits", "results"):
            items = value.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        data = value.get("data")
        if isinstance(data, dict):
            return extract_records(data)
    fail("adapter-record payload must contain a list, records, hits, results, or data.records")


def policy_decision(record: dict[str, Any]) -> str:
    decision = record.get("policy_decision")
    if isinstance(decision, dict):
        return str(decision.get("decision", "unknown"))
    return "unknown"


def field_text(record: dict[str, Any]) -> str:
    fields = [
        record.get("record_id", ""),
        record.get("record_type", ""),
        record.get("title", ""),
        record.get("object_kind", ""),
        record.get("path_ref", ""),
        record.get("snippet", ""),
        " ".join(str(tag) for tag in record.get("handling_tags", []) if tag is not None)
        if isinstance(record.get("handling_tags"), list)
        else "",
        json.dumps(record.get("source", {}), sort_keys=True),
    ]
    return " ".join(str(field) for field in fields if field is not None)


def score(record: dict[str, Any], query: str) -> float:
    q_tokens = tokens(query)
    if not q_tokens:
        return 0.0
    text = field_text(record).lower()
    text_tokens = set(tokens(text))
    title = str(record.get("title", "")).lower()
    path_ref = str(record.get("path_ref", "")).lower()
    exact = query.lower() in text
    overlap = sum(1 for token in q_tokens if token in text_tokens)
    partial = sum(1 for token in q_tokens if token in text)
    title_hits = sum(1 for token in q_tokens if token in title)
    path_hits = sum(1 for token in q_tokens if token in path_ref)
    kind_boost = KIND_BOOST.get(str(record.get("object_kind", "")), 1.0)
    type_boost = RECORD_TYPE_BOOST.get(str(record.get("record_type", "")), 1.0)
    policy = POLICY_PENALTY.get(policy_decision(record), -0.2)
    local_only_bonus = 0.4 if record.get("classification") == "local_only" else 0.0
    return (
        (4.0 if exact else 0.0)
        + overlap * 2.0
        + partial * 0.6
        + title_hits * 1.2
        + path_hits * 1.0
        + math.log1p(kind_boost)
        + math.log1p(type_boost)
        + policy
        + local_only_bonus
    )


def evidence_refs(record: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("record_id", "path_ref", "metadata_hash", "content_hash"):
        value = record.get(key)
        if isinstance(value, str) and value:
            refs.append(f"{key}:{value}")
    source = record.get("source")
    if isinstance(source, dict):
        system = source.get("system")
        repo = source.get("repo")
        if system:
            refs.append(f"source.system:{system}")
        if repo:
            refs.append(f"source.repo:{repo}")
    return refs


def explain(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record.get("record_id"),
        "record_type": record.get("record_type"),
        "title": record.get("title"),
        "object_kind": record.get("object_kind"),
        "path_ref": record.get("path_ref"),
        "snippet": record.get("snippet"),
        "handling_tags": record.get("handling_tags", []),
        "classification": record.get("classification"),
        "policy_decision": record.get("policy_decision", {}),
        "source": record.get("source", {}),
        "evidence_refs": evidence_refs(record),
    }


def search(records: list[dict[str, Any]], query: str, limit: int) -> dict[str, Any]:
    ranked: list[tuple[float, dict[str, Any]]] = []
    for record in records:
        value = score(record, query)
        if value > 0:
            ranked.append((value, record))
    ranked.sort(key=lambda pair: (-pair[0], str(pair[1].get("record_type", "")), str(pair[1].get("record_id", ""))))
    results = []
    for value, record in ranked[:limit]:
        item = explain(record)
        item["score"] = round(value, 4)
        results.append(item)
    return {
        "query": query,
        "mode": "lampstand-adapter-record-evidence-v0",
        "source_authority": "Lampstand adapter_records",
        "result_count": len(results),
        "results": results,
        "notice": "Results are local adapter-record evidence, not durable Memory Mesh promotion or semantic certainty.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Lampstand adapter records as Sherlock evidence packets.")
    parser.add_argument("--index", required=True, help="Path to Lampstand adapter-record JSON or query response JSON")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results")
    parser.add_argument("--out", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    records = extract_records(load_payload(Path(args.index)))
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
