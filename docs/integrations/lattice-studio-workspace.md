# Lattice Studio Workspace Search Handoff

Sherlock Search consumes Lattice Studio workspace outputs as `lattice.platformAssetRecord` documents.

## Source of truth

The canonical identity object remains:

```text
PlatformAssetRecord
```

Lattice Studio may emit an enrichment sidecar:

```text
PlatformAssetRecordEnrichmentSet
```

Sherlock should index the `search` envelope from each enrichment and preserve the canonical `assetId`, `assetKind`, `producerRepo`, `policyRef`, `evidenceCorrelationId`, and `compatibilitySurfaces` fields.

## Workspace synthesis fixture

A representative fixture lives at:

```text
fixtures/lattice-studio/workspace-synthesis.sherlock-doc.json
```

It represents a source-grounded workspace synthesis artifact produced from documents, sheets, slides, notebook session binding, evidence, and publication receipt.

## Required facets

Sherlock must facet these workspace-derived records by:

```text
assetKind
producerRepo
promotionChannel
sourceKind
policyRef
compatibilitySurfaces
slashTopics
governance.evidenceCompleteness
governance.searchVisibility
```

## Doctrine

Workspace synthesis is not a loose generated document. It is a governed, evidence-linked, source-grounded Lattice asset and must be searchable beside runtime, catalog, notebook, and evidence records.
