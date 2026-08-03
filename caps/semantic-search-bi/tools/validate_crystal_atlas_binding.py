#!/usr/bin/env python3
"""Validate the semantic.search <-> Crystal Atlas graph binding.

Contract-first, dependency-light (consistent with tools/validate_package.py):
- the binding YAML parses and declares the 3 participants;
- in-repo participant contract paths exist (search_surface, graph_backend);
- the forward field_map covers the Crystal Atlas required graph shape (nodes+edges)
  and consumes the sherlock assertion triple (subject/predicate/object);
- forward + reverse invariants are present.

The Crystal Atlas contract lives in another repo (prophet-platform); it is
referenced by path+version and NOT resolved here (cross-repo reference is by
contract, not by local file).
"""
from __future__ import annotations
import sys
from pathlib import Path

CAP = Path(__file__).resolve().parents[1]           # caps/semantic-search-bi
REPO = Path(__file__).resolve().parents[3]          # repo root
BINDING = CAP / "bindings" / "crystal-atlas-graph.binding.v0.yaml"

try:
    import yaml
except Exception as exc:  # pragma: no cover
    print(f"ERROR: PyYAML required: {exc}", file=sys.stderr); sys.exit(2)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}"); raise SystemExit(1)


def main() -> int:
    if not BINDING.exists():
        fail(f"missing binding: {BINDING}")
    b = yaml.safe_load(BINDING.read_text())

    parts = b.get("participants", {})
    for key in ("search_surface", "graph_backend", "crystal_atlas"):
        if key not in parts:
            fail(f"participants.{key} missing")

    # in-repo participant paths must exist (crystal_atlas is cross-repo -> skip)
    for key in ("search_surface", "graph_backend"):
        p = REPO / parts[key]["path"]
        if not p.exists():
            fail(f"participants.{key}.path does not exist in repo: {parts[key]['path']}")

    fwd = b.get("forward", {})
    tos = {m.get("to", "").split("[")[0].split(".")[0] for m in fwd.get("field_map", [])}
    for req in ("nodes", "edges", "evidence"):
        if req not in tos:
            fail(f"forward.field_map does not populate Crystal Atlas '{req}'")
    froms = " ".join(m.get("from", "") for m in fwd.get("field_map", []))
    for spo in ("assertion.subject", "assertion.predicate", "assertion.object"):
        if spo not in froms:
            fail(f"forward.field_map does not consume sherlock '{spo}'")

    if not fwd.get("invariants"):
        fail("forward.invariants missing")
    if not b.get("reverse", {}).get("invariants"):
        fail("reverse.invariants missing")
    if b.get("policy", {}).get("policy_guard") != "default-deny":
        fail("policy.policy_guard must be default-deny")

    print("OK: crystal-atlas graph binding valid "
          f"({len(fwd.get('field_map', []))} field maps; "
          f"{len(fwd.get('invariants', []))} forward + "
          f"{len(b['reverse']['invariants'])} reverse invariants).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
