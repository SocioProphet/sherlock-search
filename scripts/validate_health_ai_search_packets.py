#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "health-ai-search-packet.schema.json"
EXAMPLES = [
    ROOT / "examples" / "health-ai" / "clinical-value-source-search-packet.example.json",
    ROOT / "examples" / "health-ai" / "health-eval-design-search-packet.example.json",
]
FORBIDDEN = ["healthbench:"]

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    errors: list[str] = []

    try:
        schema = load_json(SCHEMA)
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        print(f"ERR: invalid schema: {exc}", file=sys.stderr)
        return 2

    for path in EXAMPLES:
        try:
            packet = load_json(path)
            Draft202012Validator(schema).validate(packet)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)} failed schema validation: {exc}")
            continue

        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN:
            if forbidden in text:
                errors.append(f"{path.relative_to(ROOT)} contains forbidden benchmark leakage marker")

        if packet.get("production_ready") is not False:
            errors.append(f"{path.relative_to(ROOT)} production_ready must be false")
        if packet.get("patient_care_action") is not False:
            errors.append(f"{path.relative_to(ROOT)} patient_care_action must be false")
        if packet.get("customer_facing_claim") is not False:
            errors.append(f"{path.relative_to(ROOT)} customer_facing_claim must be false")

        boundary = packet.get("facets", {}).get("benchmark_boundary", {})
        for key in ("protected_examples_reproduced", "answer_keys_reproduced", "canary_reproduced"):
            if boundary.get(key) is not False:
                errors.append(f"{path.relative_to(ROOT)} {key} must be false")

        if packet.get("source_class") == "external_competitor_claim":
            if "ambience_healthcare" not in packet.get("source_material", []):
                errors.append("external competitor claim must cite ambience_healthcare source material")
        if packet.get("source_class") == "benchmark_design_claim":
            if "healthbench_openai" not in packet.get("source_material", []):
                errors.append("benchmark design claim must cite healthbench_openai source material")

    if errors:
        print("ERR: Health AI search packet validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    print("Health AI search packets validate.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
