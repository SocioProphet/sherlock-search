#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCHER = ROOT / "tools/search_prophet_understanding.py"


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def index_records() -> list[dict[str, object]]:
    return [
        {
            "repo_full_name": "SocioProphet/sherlock-fixture",
            "repo_commit": "abcdef1",
            "schema_version": "prophet-understanding.v0",
            "record_family": "repo_graph_node",
            "record_id": "contract:demo",
            "title": "contract: demo contract",
            "text": "demo contract at contracts/demo.json",
            "node_id": "contract:demo",
            "path": "contracts/demo.json",
            "confidence": 1.0,
            "policy_state": "allow",
            "provenance_receipt_ids": ["receipt:contract"],
            "raw": {},
        },
        {
            "repo_full_name": "SocioProphet/sherlock-fixture",
            "repo_commit": "abcdef1",
            "schema_version": "prophet-understanding.v0",
            "record_family": "repo_graph_edge",
            "record_id": "edge:schema-validates-contract",
            "title": "validates: schema:demo -> contract:demo",
            "text": "validates relationship from demo schema to demo contract",
            "edge_id": "edge:schema-validates-contract",
            "source_node_id": "schema:demo",
            "target_node_id": "contract:demo",
            "confidence": 1.0,
            "policy_state": "allow",
            "provenance_receipt_ids": ["receipt:edge"],
            "raw": {},
        },
        {
            "repo_full_name": "SocioProphet/sherlock-fixture",
            "repo_commit": "abcdef1",
            "schema_version": "prophet-understanding.v0",
            "record_family": "repo_graph_policy",
            "record_id": "policy:demo",
            "title": "policy: allow",
            "text": "demo policy allows graph-backed review",
            "policy_state": "allow",
            "provenance_receipt_ids": ["receipt:policy"],
            "raw": {},
        },
    ]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sherlock-prophet-understand-") as raw_tmp:
        tmp = Path(raw_tmp)
        index = tmp / "index.json"
        out = tmp / "search.json"
        index.write_text(json.dumps(index_records(), indent=2, sort_keys=True), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SEARCHER), "--index", str(index), "--query", "what validates this contract?", "--out", str(out)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            fail("search helper exited nonzero")
        if not out.exists():
            fail("search helper did not create output")
        payload = json.loads(out.read_text(encoding="utf-8"))
        if payload.get("mode") != "lexical-graph-evidence-v0":
            fail("search result mode drifted")
        if payload.get("result_count", 0) < 1:
            fail("search returned no results")
        first = payload["results"][0]
        if not first.get("provenance_receipt_ids"):
            fail("top result does not preserve provenance")
        print("OK: Sherlock Prophet Understand search smoke passed")


if __name__ == "__main__":
    main()
