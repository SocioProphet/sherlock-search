# Complies with Standards — Multi-Domain Geospatial Intelligence

Status: Draft discovery conformance

This search/discovery repository consumes the SocioProphet multi-domain geospatial standards package.

## Standards consumed

- `SocioProphet/prophet-platform-standards/docs/standards/070-multidomain-geospatial-standards-alignment.md`
- `SocioProphet/prophet-platform-standards/registry/multidomain-geospatial-standards-map.v1.json`
- `SocioProphet/socioprophet-standards-storage/docs/standards/096-multidomain-geospatial-storage-contracts.md`
- `SocioProphet/socioprophet-standards-knowledge/docs/standards/080-multidomain-geospatial-knowledge-context.md`
- `SocioProphet/socioprophet-agent-standards/docs/standards/020-multidomain-geospatial-agent-runtime.md`

## Implementation responsibility

`Sherlock Search` owns discovery records and search result fixtures for multi-domain geospatial artifacts.

Discovery records SHOULD preserve:

- source record references
- knowledge artifact references
- provenance and evidence refs
- map/layer refs
- privacy and safety tier
- license/attribution refs
- runtime boundary refs where applicable

## Required discovery examples

- satellite asset/product discovery
- vessel track discovery
- air track discovery
- sensor/fusion event discovery
- sensitive geospatial policy discovery
- decision-card discovery

## Promotion gate

Sherlock discovery fixtures are draft until they reference the storage and knowledge standards and include governance metadata for sensitive geospatial content.
