# Sherlock Search: SCOPE-D Graph Index v0.1

This slice gives Sherlock Search a deterministic indexing path for SCOPE-D cyber graph exports.

## Input

Sherlock consumes a `CyberGraphExport` from SCOPE-D.

The expected upstream path is:

```text
SCOPE-D Intelligence Fabric
  -> SCOPE-D Arsenal candidate export
  -> SCOPE-D Cyber Graph Export
  -> Sherlock Graph Index
```

## Indexed objects

Sherlock indexes graph nodes and graph edges as evidence documents.

Node classes:

- indicator
- provider
- observation
- evidence receipt
- detection candidate
- rule family
- ATT&CK technique
- deployment target
- agent workflow
- edge bastion

Edge classes:

- enrichment
- receipt production
- observation production
- candidate generation
- ATT&CK mapping
- rule-family usage
- deployment targeting
- model-review workflow
- CloudShell Fog eligibility
- evidence grounding

## Ranking signals

Each document carries:

- evidence strength
- graph connectivity
- operational priority
- confidence

Search is lexical in v0.1 but rank-aware. This provides a stable interface before vector/hybrid retrieval lands.

## CloudShell Fog

CloudShell Fog nodes and edges are indexed as edge-bastion and deployment-related documents. Sherlock should treat these as operator-assurance surfaces, not autonomous execution targets.

## Arsenal terminology

Detection generation is referred to as Arsenal in Sherlock-facing tags. This replaces the weaker “detection factory” framing.

## Commands

```bash
npm run test:scope-d-graph
npm test
```

## Next slices

1. Add file-based CLI for indexing exported SCOPE-D graph JSON.
2. Add route-level query API.
3. Add vector-ready chunk metadata.
4. Add provenance-aware result rendering.
5. Add Noetica workspace query endpoint.
6. Add SynapseIQ evidence packet query endpoint.
