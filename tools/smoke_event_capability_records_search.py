#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCHER = ROOT / "tools/search_event_capability_records.py"


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def event_capability_records() -> list[dict[str, object]]:
    return [
        {
            "record_id": "record:cool-room-with-fan",
            "mode": "event-capability-evidence-v0",
            "event": {
                "event_id": "event:sensor:living-room-temp-high",
                "event_type": "sensor.threshold_crossed",
                "target_node_id": "node:living-room-fan-01",
                "payload": {"metric": "temperature_f", "value": 78.4, "threshold": 76},
                "causality": {"idempotency_key": "idem:fan", "policy_epoch": "policy-epoch-0"},
            },
            "capability": {
                "capability_id": "capability:cool-room-with-fan",
                "display_name": "Cool room with fan when hot",
                "effect_class": "low_risk_actuation",
                "required_policy_outcome": "allowed",
            },
            "reaction": {
                "reaction_id": "reaction:cool-room-with-fan",
                "policy_outcome": "allowed",
                "status": "scheduled",
            },
            "evidence_refs": ["receipt:event:living-room-temp-high", "receipt:policy:allow-cool-living-room"],
        },
        {
            "record_id": "record:security-arm-needs-approval",
            "mode": "event-capability-evidence-v0",
            "event": {
                "event_id": "event:agent:propose-arm-security",
                "event_type": "agent.plan_proposed",
                "target_node_id": "node:security-system-01",
                "payload": {"requested_action": "arm_alarm"},
                "causality": {"idempotency_key": "idem:security", "policy_epoch": "policy-epoch-0"},
            },
            "capability": {
                "capability_id": "capability:arm-security-system",
                "display_name": "Arm household security system",
                "effect_class": "high_risk_actuation",
                "required_policy_outcome": "requires_approval",
            },
            "reaction": {
                "reaction_id": "reaction:security-arm-needs-approval",
                "policy_outcome": "requires_approval",
                "status": "blocked_or_waiting",
            },
            "evidence_refs": ["receipt:agent:propose-arm-security", "receipt:policy:requires-approval-arm-security"],
        },
        {
            "record_id": "record:block-camera-media-release",
            "mode": "event-capability-evidence-v0",
            "event": {
                "event_id": "event:agent:request-camera-media-release",
                "event_type": "agent.plan_proposed",
                "target_node_id": "node:front-door-camera-01",
                "payload": {"requested_action": "camera_media_release"},
                "causality": {"idempotency_key": "idem:camera-media", "policy_epoch": "policy-epoch-0"},
            },
            "capability": {
                "capability_id": "capability:block-camera-media-release",
                "display_name": "Block camera media release",
                "effect_class": "high_risk_actuation",
                "required_policy_outcome": "denied",
            },
            "reaction": {
                "reaction_id": "reaction:block-camera-media-release",
                "policy_outcome": "denied",
                "status": "blocked_or_waiting",
            },
            "evidence_refs": ["receipt:policy:deny-camera-media-release"],
        },
    ]


def run_search(index: Path, query: str, out: Path) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SEARCHER), "--index", str(index), "--query", query, "--out", str(out)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        fail("event capability search helper exited nonzero")
    if not out.exists():
        fail("search helper did not create output")
    payload = json.loads(out.read_text(encoding="utf-8"))
    if payload.get("mode") != "event-capability-evidence-v0":
        fail("search result mode drifted")
    if payload.get("result_count", 0) < 1:
        fail("search returned no results")
    return payload


def assert_top(payload: dict[str, object], *, outcome: str, capability_id: str) -> None:
    top = payload["results"][0]
    if top.get("policy_outcome") != outcome:
        fail(f"top result policy outcome drifted: expected {outcome}, got {top.get('policy_outcome')}")
    if top.get("capability_id") != capability_id:
        fail(f"top result capability drifted: expected {capability_id}, got {top.get('capability_id')}")
    for key in ("event_id", "reaction_id", "idempotency_key", "policy_epoch", "receipt_refs", "evidence_refs"):
        if not top.get(key):
            fail(f"top result missing {key}")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sherlock-event-capability-") as raw_tmp:
        tmp = Path(raw_tmp)
        index = tmp / "records.json"
        index.write_text(json.dumps({"records": event_capability_records()}, indent=2, sort_keys=True), encoding="utf-8")

        security = run_search(index, "security approval", tmp / "security.json")
        assert_top(security, outcome="requires_approval", capability_id="capability:arm-security-system")

        camera = run_search(index, "camera media denied", tmp / "camera.json")
        assert_top(camera, outcome="denied", capability_id="capability:block-camera-media-release")

        fan = run_search(index, "fan temperature allowed", tmp / "fan.json")
        assert_top(fan, outcome="allowed", capability_id="capability:cool-room-with-fan")

        print("OK: Sherlock event-capability search smoke passed")


if __name__ == "__main__":
    main()
