#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCHER = ROOT / "tools/search_lampstand_adapter_records.py"


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def adapter_records() -> list[dict[str, object]]:
    return [
        {
            "record_id": "lampstand-adapter-record::sha256:repo-context",
            "record_type": "sourceos.lampstand.repo_context_record.v1",
            "title": "Repo context: smart-tree",
            "object_kind": "repo_context",
            "path_ref": "~/dev/smart-tree",
            "metadata_hash": "sha256:context",
            "snippet": "Bounded Smart Tree repo context for sourceos-context adapter.",
            "handling_tags": ["local-only", "repo-context", "smart-tree"],
            "classification": "local_only",
            "policy_decision": {"decision": "allow", "ruleset": "sourceos.repo_context.read_only"},
            "source": {"system": "sourceos-smart-tree-adapter", "repo": "SocioProphet/smart-tree"},
        },
        {
            "record_id": "lampstand-adapter-record::sha256:security",
            "record_type": "sourceos.lampstand.security_search_record.v1",
            "title": "Security signal: untrusted hook",
            "object_kind": "security_signal",
            "path_ref": "settings.json",
            "metadata_hash": "sha256:security",
            "snippet": "Advisory security signal produced by Smart Tree.",
            "handling_tags": ["local-only", "security-advisory", "smart-tree"],
            "classification": "local_only",
            "policy_decision": {"decision": "allow", "ruleset": "sourceos.repo_context.read_only"},
            "source": {"system": "sourceos-smart-tree-adapter", "repo": "SocioProphet/smart-tree"},
        },
        {
            "record_id": "lampstand-adapter-record::sha256:memory",
            "record_type": "sourceos.lampstand.memory_candidate_record.v1",
            "title": "Memory candidate: repo_onboarding",
            "object_kind": "memory_candidate",
            "path_ref": "~/dev/smart-tree",
            "metadata_hash": "sha256:memory",
            "snippet": "Repo onboarding candidate generated from bounded Smart Tree scan.",
            "handling_tags": ["local-only", "memory-candidate", "smart-tree"],
            "classification": "local_only",
            "policy_decision": {"decision": "allow", "ruleset": "sourceos.repo_context.read_only"},
            "source": {"system": "sourceos-smart-tree-adapter", "repo": "SocioProphet/smart-tree"},
        },
    ]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sherlock-lampstand-records-") as raw_tmp:
        tmp = Path(raw_tmp)
        index = tmp / "records.json"
        out = tmp / "search.json"
        index.write_text(json.dumps({"records": adapter_records()}, indent=2, sort_keys=True), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SEARCHER), "--index", str(index), "--query", "smart-tree repo context", "--out", str(out)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            fail("Lampstand adapter-record search helper exited nonzero")
        if not out.exists():
            fail("search helper did not create output")
        payload = json.loads(out.read_text(encoding="utf-8"))
        if payload.get("mode") != "lampstand-adapter-record-evidence-v0":
            fail("search result mode drifted")
        if payload.get("source_authority") != "Lampstand adapter_records":
            fail("source authority drifted")
        if payload.get("result_count", 0) < 1:
            fail("search returned no results")
        top = payload["results"][0]
        if top.get("object_kind") != "repo_context":
            fail("top result should be repo context for repo context query")
        if not top.get("evidence_refs"):
            fail("top result lacks evidence refs")
        if top.get("source", {}).get("system") != "sourceos-smart-tree-adapter":
            fail("source system was not preserved")
        if top.get("policy_decision", {}).get("ruleset") != "sourceos.repo_context.read_only":
            fail("policy ruleset was not preserved")
        print("OK: Sherlock Lampstand adapter-record search smoke passed")


if __name__ == "__main__":
    main()
