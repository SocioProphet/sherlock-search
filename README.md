# sherlock-search

Canonical repo for Sherlock-related search/discovery work.

## Lampstand adapter-record search

Sherlock can now consume Lampstand governed adapter records as local evidence packets.

The search helper and smoke test live at:

- `tools/search_lampstand_adapter_records.py`
- `tools/smoke_lampstand_adapter_records_search.py`

Validate locally:

```bash
python tools/smoke_lampstand_adapter_records_search.py
```

This lane consumes records produced through Lampstand's `adapter_records` authority, including Smart Tree records published by `sourceos-context lampstand-publish --publish`. It preserves `policy_decision`, `source`, `classification`, `handling_tags`, and generated evidence refs. It does not claim durable Memory Mesh promotion or semantic/vector certainty.

## Professional Intelligence search packets

Sherlock now carries the first validated search-packet surface for the Professional Intelligence OS Gate 3 demo path.

The search packet contract and example live at:

- `schemas/professional-intelligence-search-packet.schema.json`
- `examples/professional-intelligence/search-packet.example.json`

Validate locally:

```bash
python -m pip install jsonschema
python scripts/validate_professional_intelligence_search_packet.py
```

The workflow `.github/workflows/professional-intelligence-search-packet.yml` runs this validation when the search-packet schema, example, validator, or workflow changes.

The seed packet provides workroom-scoped retrieval context for Memory Mesh context packs, Agentplane workflow evidence, Prophet Workspace workrooms, Policy Fabric decisions, and ContractForge obligations.

## Personal Intelligence Cell search packets

Sherlock can now consume a Personal Intelligence Cell search packet that is compatible with the existing Professional Intelligence search-packet schema.

The example and validator live at:

- `examples/personal-intelligence-cell/search-packet.example.json`
- `scripts/validate_personal_intelligence_cell_search_packet.py`

Validate locally:

```bash
python scripts/validate_personal_intelligence_cell_search_packet.py
```

This packet maps `prophet-platform` cell-service lineage into Sherlock search/discovery:

```text
Cell -> Watch -> Signal -> FeedItem -> SherlockSearchPacket
```

It preserves workroom scope, playbook ID, policy decision refs, citation refs, evidence refs, result confidence, freshness, and sensitivity ceiling.

## Computational artifact search packets

Sherlock now includes a validated indexing path for Prophet computational artifact evidence packets.

The schema, example, and validator live at:

- `schemas/computational-artifact-search-packet.schema.json`
- `examples/computational-artifact/search-packet.example.json`
- `scripts/validate_computational_artifact_search_packet.py`

Validate locally:

```bash
python -m pip install jsonschema
python scripts/validate_computational_artifact_search_packet.py
```

The workflow `.github/workflows/computational-artifact-search-packet.yml` validates this packet when the schema/example/validator path changes.

After Prophet Platform executes `artifact://gaia.bounded-osm-ingest@0.1.0`, it emits this packet for Sherlock indexing with artifact ID, owner repo, runtime profile, safety class, provenance/source receipt refs, validation report refs, benchmark metric refs, lineage refs, citation refs, evidence refs, policy decision refs, freshness, and sensitivity ceilings.

Sherlock retrieval remains evidence-grounded: Holmes can apply semantic interpretation over these indexed packets, while Sociosphere registry health checks can verify cited source and lineage readiness without asserting vector/semantic certainty at indexing time.

## Dossier pointers (2026-04-12)

- Full conversation dossier (Drive Doc ID): 1nxHeAZXSmvXtjg8jU2ZfpzloleO0_VIVDsRefoNYgSM
- Semantic architecture paste capture (Drive Doc ID): 1BmUHsdRD6ctbpkYVosKK12NOvrQZj7TG_Nfe3jOBems

A versioned repo copy of the dossier lives under `docs/dossiers/agentic-marketing-2026-04-12/`.
