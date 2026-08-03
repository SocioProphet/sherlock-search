#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, sys
def fail(m): print("ERR:", m, file=sys.stderr); sys.exit(2)
def okp(m): print("OK:", m)
def lj(p):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception as e: fail(f"json parse failed for {p}: {e}")
def ly(p):
    import yaml; return yaml.safe_load(Path(p).read_text(encoding="utf-8"))
def main():
    pkg = Path(__file__).resolve().parents[1]
    for d in ("capd","docs","rpc","schemas","tools","topics","policy","examples"):
        if not (pkg/d).is_dir(): fail(f"missing dir: {d}")
    okp("package structure looks sane")
    cap = ly(pkg/"capd"/"capability.yaml").get("capability", {})
    if cap.get("kind") != "contract-only": fail("capability.kind must be contract-only")
    if cap.get("name") != "search.preprocess.contextual": fail("capability.name must be search.preprocess.contextual")
    okp("capd semantics validated")
    rpc = ly(pkg/"rpc"/"contextual.preprocess.v0.yaml").get("methods") or {}
    for m in ("Situate","GetStatus"):
        if m not in rpc: fail(f"rpc missing method: {m}")
    okp("rpc semantics validated")
    tn = {t.get("name") for t in (ly(pkg/"topics"/"contextual.preprocess.topics.v0.yaml").get("topics") or [])}
    if "governance.evidence.emitted" not in tn: fail("topics must include governance.evidence.emitted")
    okp("topics semantics validated")
    for s in sorted((pkg/"schemas").glob("*.schema.json")):
        o = lj(s)
        if "$schema" not in o or "type" not in o: fail(f"{s} not a JSON Schema")
    okp("json schemas parse")
    # teeth: response example must validate against contextual_chunk shape (required fields present)
    resp = lj(pkg/"examples"/"situate.response.json")
    req = {"chunk_id","parent_doc_id","chunk_text","situating_context","situated_text","index_targets"}
    for ch in resp["chunks"]:
        missing = req - set(ch)
        if missing: fail(f"example chunk missing {missing}")
        if ch["situated_text"] == ch["chunk_text"]: fail("situated_text must prepend context, not equal chunk_text")
    okp("example contextual chunks carry situating context (teeth)")
    okp("capability package validates")
if __name__ == "__main__": main()
