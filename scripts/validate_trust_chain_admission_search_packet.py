#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "trust-chain-admission-search-packet.v0.1.schema.json"
ALLOW_FIXTURE = ROOT / "examples" / "trust-chain" / "admission-search-packet.allow.json"
DENIED_FIXTURE = ROOT / "examples" / "trust-chain" / "admission-search-packet.denied.json"


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_matches(value: Any, expected: str) -> bool:
    actual = json_type_name(value)
    if expected == "number":
        return actual in {"integer", "number"}
    return actual == expected


def validate_schema(schema: dict[str, Any], value: Any, path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        fail(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        fail(f"{path}: {value!r} not in enum {schema['enum']!r}")
    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(value, item) for item in expected_types):
            fail(f"{path}: expected type {expected_types!r}, got {json_type_name(value)!r}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                fail(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                fail(f"{path}: unexpected properties {extra!r}")
        additional = schema.get("additionalProperties")
        for key, item in value.items():
            child_schema = properties.get(key)
            if child_schema is None and isinstance(additional, dict):
                child_schema = additional
            if child_schema is not None:
                validate_schema(child_schema, item, f"{path}.{key}")
    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                validate_schema(item_schema, item, f"{path}[{index}]")


def validate_allow(packet: dict[str, Any], path: Path) -> None:
    if packet.get("decision") != "allow":
        fail(f"{path}: allow fixture requires decision=allow")
    if packet.get("query_facets", {}).get("remediation_required") is not False:
        fail(f"{path}: allow fixture must not require remediation")
    if packet.get("query_facets", {}).get("missing_evidence") != []:
        fail(f"{path}: allow fixture must not report missing evidence")
    if not packet.get("receipt_refs"):
        fail(f"{path}: allow fixture requires receipt_refs")
    if packet.get("remediation") != []:
        fail(f"{path}: allow fixture remediation must be empty")
    for ref in ("sbom://", "vex://", "scan://", "policy://", "guardrail:", "agentplane:"):
        if not any(str(item).startswith(ref) for item in packet.get("evidence_refs", [])):
            fail(f"{path}: allow fixture missing evidence prefix {ref}")


def validate_denied(packet: dict[str, Any], path: Path) -> None:
    if packet.get("decision") != "deny":
        fail(f"{path}: denied fixture requires decision=deny")
    if packet.get("query_facets", {}).get("remediation_required") is not True:
        fail(f"{path}: denied fixture must require remediation")
    missing = packet.get("query_facets", {}).get("missing_evidence", [])
    if not isinstance(missing, list) or not missing:
        fail(f"{path}: denied fixture must expose missing_evidence facets")
    remediation = packet.get("remediation", [])
    if not isinstance(remediation, list) or not remediation:
        fail(f"{path}: denied fixture requires remediation")
    for item in remediation:
        if not item.get("authority"):
            fail(f"{path}: remediation requires authority")
        if item.get("required_before_admission") is not True:
            fail(f"{path}: remediation must be required before admission")
    if packet.get("receipt_refs") != []:
        fail(f"{path}: denied fixture must not carry runtime receipts")


def main() -> int:
    try:
        schema = load_json(SCHEMA)
        allow = load_json(ALLOW_FIXTURE)
        denied = load_json(DENIED_FIXTURE)
        validate_schema(schema, allow)
        validate_schema(schema, denied)
        validate_allow(allow, ALLOW_FIXTURE)
        validate_denied(denied, DENIED_FIXTURE)
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2
    print("OK: Trust Chain admission search packets passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
