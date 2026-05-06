#!/usr/bin/env python3
"""Search embodied orchestration traces as Sherlock evidence packets.

This consumes the record export produced by:

  python specs/orchestration/embodied_experience_trace_fixture.py --records

It also accepts full trace bundles that contain a top-level `traces` list. The
search mode is deliberately deterministic and stdlib-only so it can run in CI,
agent workcells, and SourceOS local-first bootstrap environments.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

TASK_BOOST = {
    "track_count": 2.0,
    "track_permanence": 2.0,
    "plan_generation": 1.8,
    "policy_aware_planning": 2.2,
}
POLICY_BOOST = {
    "denied": 1.4,
    "requires_approval": 1.3,
    "allowed": 0.5,
    "redacted": 0.8,
    "degraded": 0.8,
}


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def tokens(text: str) -> list[str]:
    return [part for part in re.split(r"[^A-Za-z0-9_.:/-]+", text.lower()) if part]


def load_payload(path: Path) -> Any:
    if not path.exists():
        fail(f"missing trace index: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid trace JSON: {exc}")


def extract_records(value: Any) -> list[dict[str, Any]]:
    """Accept record exports, trace bundles, and simple result envelopes."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        records = value.get("records") or value.get("results")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)]
        traces = value.get("traces")
        if isinstance(traces, list):
            return [trace_to_record(item) for item in traces if isinstance(item, dict)]
        data = value.get("data")
        if isinstance(data, dict):
            return extract_records(data)
    fail("trace payload must contain records, results, traces, data.records, or a top-level list")


def trace_to_record(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": "record:" + str(trace.get("trace_id", "unknown")).split(":", 1)[-1],
        "task_family": trace.get("task_family"),
        "input": {
            "goal": trace.get("goal"),
            "steps": trace.get("steps", []),
            "query": trace.get("query"),
        },
        "target": trace.get("expected_answer", {}),
        "state_assertions": trace.get("state_assertions", []),
        "receipt_refs": trace.get("receipt_refs", []),
    }


def field_text(record: dict[str, Any]) -> str:
    parts = [
        record.get("record_id", ""),
        record.get("task_family", ""),
        json.dumps(record.get("input", {}), sort_keys=True),
        json.dumps(record.get("target", {}), sort_keys=True),
        json.dumps(record.get("state_assertions", []), sort_keys=True),
        " ".join(str(ref) for ref in record.get("receipt_refs", []) if ref is not None)
        if isinstance(record.get("receipt_refs"), list)
        else "",
    ]
    return " ".join(str(part) for part in parts if part is not None)


def policy_outcomes(record: dict[str, Any]) -> list[str]:
    outcomes: list[str] = []
    target = record.get("target")
    if isinstance(target, dict):
        value = target.get("policy_outcomes")
        if isinstance(value, list):
            outcomes.extend(str(item) for item in value if item is not None)
    input_obj = record.get("input")
    if isinstance(input_obj, dict):
        for step in input_obj.get("steps", []) or []:
            if isinstance(step, dict) and step.get("policy_outcome"):
                outcomes.append(str(step["policy_outcome"]))
    return outcomes


def score(record: dict[str, Any], query: str) -> float:
    q_tokens = tokens(query)
    if not q_tokens:
        return 0.0
    text = field_text(record).lower()
    text_tokens = set(tokens(text))
    exact = query.lower() in text
    overlap = sum(1 for token in q_tokens if token in text_tokens)
    partial = sum(1 for token in q_tokens if token in text)
    task = str(record.get("task_family", ""))
    task_bonus = math.log1p(TASK_BOOST.get(task, 1.0))
    policy_bonus = sum(POLICY_BOOST.get(outcome, 0.0) for outcome in set(policy_outcomes(record)))
    receipt_bonus = 0.5 if record.get("receipt_refs") else 0.0
    return (4.0 if exact else 0.0) + overlap * 2.0 + partial * 0.5 + task_bonus + policy_bonus + receipt_bonus


def evidence_refs(record: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    if record.get("record_id"):
        refs.append("record_id:" + str(record["record_id"]))
    for receipt in record.get("receipt_refs", []) or []:
        refs.append("receipt:" + str(receipt))
    target = record.get("target")
    if isinstance(target, dict):
        for key in ("answer_type", "value", "object_id"):
            if target.get(key) is not None:
                refs.append(f"target.{key}:{target[key]}")
    return refs


def explain(record: dict[str, Any]) -> dict[str, Any]:
    input_obj = record.get("input") if isinstance(record.get("input"), dict) else {}
    return {
        "record_id": record.get("record_id"),
        "task_family": record.get("task_family"),
        "goal": input_obj.get("goal"),
        "query": input_obj.get("query"),
        "step_count": len(input_obj.get("steps", []) or []),
        "target": record.get("target", {}),
        "state_assertions": record.get("state_assertions", []),
        "policy_outcomes": sorted(set(policy_outcomes(record))),
        "receipt_refs": record.get("receipt_refs", []),
        "evidence_refs": evidence_refs(record),
    }


def search(records: list[dict[str, Any]], query: str, limit: int) -> dict[str, Any]:
    ranked: list[tuple[float, dict[str, Any]]] = []
    for record in records:
        value = score(record, query)
        if value > 0:
            ranked.append((value, record))
    ranked.sort(key=lambda pair: (-pair[0], str(pair[1].get("task_family", "")), str(pair[1].get("record_id", ""))))
    results = []
    for value, record in ranked[:limit]:
        item = explain(record)
        item["score"] = round(value, 4)
        results.append(item)
    return {
        "query": query,
        "mode": "embodied-orchestration-trace-evidence-v0",
        "source_authority": "Prophet Platform E2WM trace fixtures",
        "result_count": len(results),
        "results": results,
        "notice": "Results are deterministic trace evidence for embodied planning and state reasoning; live adapter certainty must be supplied by receipts.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search embodied orchestration traces as Sherlock evidence packets.")
    parser.add_argument("--index", required=True, help="Path to E2WM trace records or trace bundle JSON")
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
