# semantic.search bindings

Contract-first bindings that wire the (deliberately abstract) `semantic.search`
capability to concrete estate graph planes. Contract-only — no runtime.

## crystal-atlas-graph.binding.v0

Closes the previously-open gap where `semantic.search`'s graph backend was named
(`optional_backends.graph_atomspace`) but bound to nothing. This binding wires
three existing contracts:

```
semantic.search (ingest/enrich)
        │  assertions (subject / predicate / object, actor-attributed)
        ▼
search-backend-graph :: GraphUpsertRequest        (sherlock search lane)
        │  projected: S/P/O -> 2 nodes + 1 edge, actor+correlation -> evidence
        ▼
Crystal Atlas :: graph-upsert-request.v0          (prophet-platform intelligence lane)
        │  enrichment.emitted.v0 / entities.resolved.v0
        ▼  (reverse) reindex into semantic.search as retrievable BI signal
```

- **Forward** projection field map + invariants (no dangling edges, evidence
  required, tenant-scoped, idempotent) — see the binding YAML.
- **Reverse** subscription: Crystal Atlas enrichment/entity-resolution events
  re-index into `semantic.search`, re-running policy_guard (no redaction bypass).
- Crystal Atlas item schemas (`graph-node.v0`, `graph-edge.v0`, `claim.v0`,
  `evidence.v0`) are owned by `prophet-platform`; referenced by version, not redefined.

Validate: `python3 caps/semantic-search-bi/tools/validate_crystal_atlas_binding.py`

Status: **draft** (E1) — the participant contract *paths/versions* are real; a
runtime implementation package (triRPC, default-deny, evidence) is out of scope here.
