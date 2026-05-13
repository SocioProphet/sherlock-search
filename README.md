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

## Lawful metadata harvest search packets

Sherlock can now index lawful metadata harvesting receipts as governed search packets. The seed lane binds ProCybernetica's lawful metadata harvest contract to Sherlock discovery without treating harvested records as canonical truth.

The search packet contract, example, and validator live at:

- `schemas/lawful-metadata-harvest-search-packet.schema.json`
- `examples/harvest/lawful-metadata-harvest-search-packet.example.json`
- `scripts/validate_lawful_metadata_harvest_search_packet.py`

Validate locally:

```bash
python -m pip install jsonschema
python scripts/validate_lawful_metadata_harvest_search_packet.py
```

The workflow `.github/workflows/lawful-metadata-harvest-search-packet.yml` runs this validation when the harvest search-packet schema, example, validator, or workflow changes.

This packet preserves harvest envelope refs, policy decision refs, validation report refs, replay refs, receipt evidence refs, classification/sensitivity ceilings, handling tags, anomaly results, and promotion decisions. It intentionally indexes evidence about the harvest path; durable Memory Mesh, Knowledge Graph, GAIA, SourceOS state, or Prophet Platform promotion remains governed by explicit promotion decisions.

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

## Dossier pointers (2026-04-12)

- Full conversation dossier (Drive Doc ID): 1nxHeAZXSmvXtjg8jU2ZfpzloleO0_VIVDsRefoNYgSM
- Semantic architecture paste capture (Drive Doc ID): 1BmUHsdRD6ctbpkYVosKK12NOvrQZj7TG_Nfe3jOBems

A versioned repo copy of the dossier lives under `docs/dossiers/agentic-marketing-2026-04-12/`.
