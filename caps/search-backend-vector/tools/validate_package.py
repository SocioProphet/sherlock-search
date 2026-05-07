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


def main() -> None:
    pkg = Path(__file__).resolve().parents[1]
    for d in ("capd", "docs", "rpc", "schemas", "tools", "topics"):
        if not (pkg / d).is_dir():
            fail(f"missing dir: {d}")
    ok("package structure looks sane")

    capd = load_yaml(pkg / "capd" / "capability.yaml")
    capinfo = (capd or {}).get("capability", {})
    if capinfo.get("kind") != "contract-only":
        fail("capability.kind must be 'contract-only'")
    if capinfo.get("name") != "search.backend.vector":
        fail("capability.name must be search.backend.vector")
    ok("capd semantics validated")

    rpc = load_yaml(pkg / "rpc" / "vector.index.v0.yaml")
    methods = rpc.get("methods") or {}
    for method in ("Upsert", "Query", "GetStatus"):
        if method not in methods:
            fail(f"rpc missing method: {method}")
    ok("rpc semantics validated")

    topics = load_yaml(pkg / "topics" / "vector.index.topics.v0.yaml")
    topic_names = {t.get("name") for t in (topics.get("topics") or [])}
    if "governance.evidence.emitted" not in topic_names:
        fail("topics must include governance.evidence.emitted")
    ok("topics semantics validated")

    schemas = sorted((pkg / "schemas").glob("*.schema.json"))
    if not schemas:
        fail("no schemas/*.schema.json found")
    for s in schemas:
        obj = load_json(s)
        if "$schema" not in obj or "type" not in obj:
            fail(f"{s} does not look like a JSON Schema")
    ok("json schemas parse")
    ok("capability package validates")


if __name__ == "__main__":
    main()
