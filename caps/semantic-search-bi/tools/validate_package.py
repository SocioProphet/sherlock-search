#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import sys


def ok(msg: str) -> None:
    print("OK:", msg)


def fail(msg: str) -> None:
    print("ERR:", msg, file=sys.stderr)
    sys.exit(2)


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        fail(f"unable to read {p}: {e}")
        raise


def load_yaml(p: Path):
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        fail("PyYAML is required. Install with: python3 -m pip install pyyaml")
    try:
        return yaml.safe_load(read_text(p))
    except Exception as e:
        fail(f"yaml parse failed for {p}: {e}")


def load_json(p: Path):
    try:
        return json.loads(read_text(p))
    except Exception as e:
        fail(f"json parse failed for {p}: {e}")


def validate_json_schema(schema_path: Path) -> None:
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except ModuleNotFoundError:
        fail("jsonschema is required. Install with: python3 -m pip install jsonschema")
    schema = load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        fail(f"invalid JSON Schema {schema_path}: {e}")
    ok(f"json schema parses: {schema_path.as_posix()}")


def validate_example(example_path: Path, schema_path: Path) -> None:
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except ModuleNotFoundError:
        fail("jsonschema is required. Install with: python3 -m pip install jsonschema")
    schema = load_json(schema_path)
    example = load_json(example_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = "/".join(str(p) for p in first.path)
        fail(f"example {example_path.name} failed against {schema_path.name}: {path}: {first.message}")
    ok(f"example validates: {example_path.as_posix()} -> {schema_path.name}")


def main() -> None:
    pkg = Path(__file__).resolve().parents[1]

    required_dirs = ["capd", "docs", "examples", "rpc", "schemas", "tools", "topics"]
    for d in required_dirs:
        if not (pkg / d).is_dir():
            fail(f"missing dir: {d}")
    ok("package structure looks sane")

    capd = pkg / "capd" / "capability.yaml"
    cap = load_yaml(capd)
    capinfo = (cap or {}).get("capability", {})
    if capinfo.get("kind") != "contract-only":
        fail("capability.kind must be 'contract-only'")
    if not capinfo.get("name") or not capinfo.get("version"):
        fail("capability.name and capability.version are required")
    req = (cap or {}).get("requires", {})
    for k in ("trirpc_bus", "policy_guard", "evidence_emission"):
        if req.get(k) is not True:
            fail(f"requires.{k} must be true")
    ok("capd semantics validated")

    rpc_path = pkg / "rpc" / "semantic.search.v0.yaml"
    rpc = load_yaml(rpc_path)
    if not rpc or "service" not in rpc or "methods" not in rpc:
        fail("rpc/semantic.search.v0.yaml missing required keys")
    methods = rpc.get("methods") or {}
    for method in ("IngestDocument", "Query", "Explain", "GetStatus", "ListBackends"):
        if method not in methods:
            fail(f"rpc missing method: {method}")
    ok("rpc semantics validated")

    topics_path = pkg / "topics" / "semantic.search.topics.v0.yaml"
    topics = load_yaml(topics_path)
    topic_names = {t.get("name") for t in (topics.get("topics") or [])}
    if "governance.evidence.emitted" not in topic_names:
        fail("topics must include governance.evidence.emitted")
    ok("topics semantics validated")

    schemas_dir = pkg / "schemas"
    schemas = sorted(schemas_dir.glob("*.schema.json"))
    if not schemas:
        fail("no schemas/*.schema.json found")
    for s in schemas:
        validate_json_schema(s)

    docs_readme = read_text(pkg / "docs" / "README.md")
    if docs_readme.strip().startswith("# Title"):
        fail("docs/README.md contains placeholder content")
    rpc_text = read_text(rpc_path)
    if len(rpc_text.strip().splitlines()) < 10:
        fail("rpc spec looks truncated")

    examples = {
        "query.request.json": "query_request.schema.json",
        "query.response.json": "query_response.schema.json",
        "ingest_document.request.json": "ingest_document.schema.json",
        "explain.request.json": "explain_request.schema.json",
        "explain.response.json": "explain_response.schema.json",
        "evidence_event.allow.json": "evidence_event.schema.json",
    }
    for example_name, schema_name in examples.items():
        validate_example(pkg / "examples" / example_name, schemas_dir / schema_name)

    ok("capability package validates")


if __name__ == "__main__":
    main()
