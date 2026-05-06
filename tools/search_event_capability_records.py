#!/usr/bin/env python3
"""Search event-capability records as Sherlock evidence packets.

Consumes flattened records produced by:

  python specs/orchestration/event_capability_fixture.py --events

Also accepts a full event-capability bundle with top-level `events`,
`capabilities`, and `reaction_plans`. The output preserves event, capability,
reaction, policy outcome, idempotency, and evidence receipt references.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

EFFECT_BOOST = {
    "observe": 0.9,
    "explain": 0.9,
    "search": 0.9,
    "draft": 0.8,
    "propose": 1.0,
    "low_risk_actuation": 1.3,
    "medium_risk_actuation": 1.6,
    "high_risk_actuation": 2.0,
    "irreversible_action": 2.4,
}
OUTCOME_BOOST = {
    "allowed": 0.5,
    "denied": 1.5,
    "requires_approval": 1.4,
    "requires_local_only": 1.1,
    "redacted": 1.0,
    "degraded": 1.1,
}
EVENT_BOOST = {
    "sensor.threshold_crossed": 1.2,
    "camera.semantic_event": 1.4,
    "agent.plan_proposed": 1.6,
    "policy.decision_emitted": 1.5,
    "adapter.health_changed": 1.1,
}


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def tokens(text: str) -> list[str]:
    return [part for part in re.split(r"[^A-Za-z0-9_.:/-]+", text.lower()) if part]


def load_payload(path: Path) -> Any:
    if not path.exists():
        fail(f"missing event-capability index: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid event-capability JSON: {exc}")


def extract_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        records = value.get("records") or value.get("results")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)]
        if {"events", "capabilities", "reaction_plans"}.issubset(value):
            return bundle_to_records(value)
        data = value.get("data")
        if isinstance(data, dict):
            return extract_records(data)
    fail("payload must be a record list, records/results envelope, or full event-capability bundle")


def bundle_to_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    capabilities = {item.get("capability_id"): item for item in bundle.get("capabilities", []) if isinstance(item, dict)}
    events = {item.get("event_id"): item for item in bundle.get("events", []) if isinstance(item, dict)}
    records = []
    for reaction in bundle.get("reaction_plans", []):
        if not isinstance(reaction, dict):
            continue
        capability = capabilities.get(reaction.get("capability_id"), {})
        event = events.get(reaction.get("event_id"), {})
        records.append(
            {
                "record_id": "record:" + str(reaction.get("reaction_id", "unknown")).split(":", 1)[-1],
                "mode": "event-capability-evidence-v0",
                "event": event,
                "capability": capability,
                "reaction": reaction,
                "evidence_refs": reaction.get("receipt_refs", []),
            }
        )
    return records


def field_text(record: dict[str, Any]) -> str:
    return " ".join(
        [
            str(record.get("record_id", "")),
            json.dumps(record.get("event", {}), sort_keys=True),
            json.dumps(record.get("capability", {}), sort_keys=True),
            json.dumps(record.get("reaction", {}), sort_keys=True),
            " ".join(str(ref) for ref in record.get("evidence_refs", []) if ref is not None)
            if isinstance(record.get("evidence_refs"), list)
            else "",
        ]
    )


def score(record: dict[str, Any], query: str) -> float:
    q_tokens = tokens(query)
    if not q_tokens:
        return 0.0
    text = field_text(record).lower()
    text_tokens = set(tokens(text))
    exact = query.lower() in text
    overlap = sum(1 for token in q_tokens if token in text_tokens)
    partial = sum(1 for token in q_tokens if token in text)

    event = record.get("event") if isinstance(record.get("event"), dict) else {}
    capability = record.get("capability") if isinstance(record.get("capability"), dict) else {}
    reaction = record.get("reaction") if isinstance(record.get("reaction"), dict) else {}

    event_bonus = math.log1p(EVENT_BOOST.get(str(event.get("event_type", "")), 1.0))
    effect_bonus = math.log1p(EFFECT_BOOST.get(str(capability.get("effect_class", "")), 1.0))
    outcome_bonus = OUTCOME_BOOST.get(str(reaction.get("policy_outcome", "")), 0.0)
    evidence_bonus = 0.6 if record.get("evidence_refs") else 0.0
    idempotency_bonus = 0.4 if ((event.get("causality") or {}).get("idempotency_key")) else 0.0

    return (4.0 if exact else 0.0) + overlap * 2.0 + partial * 0.45 + event_bonus + effect_bonus + outcome_bonus + evidence_bonus + idempotency_bonus


def evidence_refs(record: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    if record.get("record_id"):
        refs.append("record_id:" + str(record["record_id"]))
    event = record.get("event") if isinstance(record.get("event"), dict) else {}
    capability = record.get("capability") if isinstance(record.get("capability"), dict) else {}
    reaction = record.get("reaction") if isinstance(record.get("reaction"), dict) else {}
    for key, obj, field in (
        ("event", event, "event_id"),
        ("capability", capability, "capability_id"),
        ("reaction", reaction, "reaction_id"),
    ):
        if obj.get(field):
            refs.append(f"{key}.{field}:{obj[field]}")
    causality = event.get("causality") if isinstance(event.get("causality"), dict) else {}
    if causality.get("idempotency_key"):
        refs.append("idempotency_key:" + str(causality["idempotency_key"]))
    for receipt in record.get("evidence_refs", []) or []:
        refs.append("receipt:" + str(receipt))
    return refs


def explain(record: dict[str, Any]) -> dict[str, Any]:
    event = record.get("event") if isinstance(record.get("event"), dict) else {}
    capability = record.get("capability") if isinstance(record.get("capability"), dict) else {}
    reaction = record.get("reaction") if isinstance(record.get("reaction"), dict) else {}
    causality = event.get("causality") if isinstance(event.get("causality"), dict) else {}
    return {
        "record_id": record.get("record_id"),
        "event_id": event.get("event_id"),
        "event_type": event.get("event_type"),
        "target_node_id": event.get("target_node_id"),
        "capability_id": capability.get("capability_id"),
        "capability_name": capability.get("display_name"),
        "effect_class": capability.get("effect_class"),
        "required_policy_outcome": capability.get("required_policy_outcome"),
        "reaction_id": reaction.get("reaction_id"),
        "reaction_status": reaction.get("status"),
        "policy_outcome": reaction.get("policy_outcome"),
        "idempotency_key": causality.get("idempotency_key"),
        "policy_epoch": causality.get("policy_epoch"),
        "receipt_refs": record.get("evidence_refs", []),
        "evidence_refs": evidence_refs(record),
    }


def search(records: list[dict[str, Any]], query: str, limit: int) -> dict[str, Any]:
    ranked: list[tuple[float, dict[str, Any]]] = []
    for record in records:
        value = score(record, query)
        if value > 0:
            ranked.append((value, record))
    ranked.sort(key=lambda pair: (-pair[0], str((pair[1].get("reaction") or {}).get("policy_outcome", "")), str(pair[1].get("record_id", ""))))
    results = []
    for value, record in ranked[:limit]:
        item = explain(record)
        item["score"] = round(value, 4)
        results.append(item)
    return {
        "query": query,
        "mode": "event-capability-evidence-v0",
        "source_authority": "Prophet Platform event-capability fixtures",
        "result_count": len(results),
        "results": results,
        "notice": "Results preserve event, capability, reaction, policy, idempotency, and receipt evidence. Live certainty must come from signed receipts.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search event-capability records as Sherlock evidence packets.")
    parser.add_argument("--index", required=True, help="Path to event-capability records or full bundle JSON")
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
