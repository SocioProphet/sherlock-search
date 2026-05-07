# Semantic Enterprise Index v0.1

Sherlock Search consumes `semantic-enterprise-v0.1.0` from `SocioProphet/ontogenesis` as search evidence.

The local fixture is:

- `examples/semantic-enterprise/v0.1/search-index.example.json`

The validator is:

- `scripts/validate_semantic_enterprise_search_index.py`

## Source release

- Repository: `SocioProphet/ontogenesis`
- Release/tag: `semantic-enterprise-v0.1.0`
- Manifest: `manifests/semantic_enterprise_v0_1_manifest.json`
- Rollup registry: `catalog/semantic_enterprise_v0_1_registry.ttl`

## Search evidence model

The v0.1 fixture indexes the five semantic-enterprise sector scenarios:

- finance
- threat intelligence
- investigation
- supply chain
- defense/C2

Each record preserves:

- source path
- query path
- named graph URI fragment
- evidence terms
- sector label
- release provenance

## Boundary

Sherlock treats Ontogenesis as authoritative source evidence. It does not promote scenario examples into runtime truth, and it preserves the distinction between source semantics, search evidence, and downstream runtime interpretation.

## Validation

Run:

```bash
make validate
```

or:

```bash
python3 scripts/validate_semantic_enterprise_search_index.py
```

## Parent work

- `SocioProphet/sherlock-search#41`
- `SocioProphet/delivery-excellence#21`
