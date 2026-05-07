# OrgGov Search Packet v0.1

## Purpose

OrgGov Search Packet v0.1 makes Sherlock the discovery and evidence-search layer for Organization Governance Control Plane v0.

The packet indexes the shared OrgGov loop:

```text
Objective → Workroom → Actor → Role → Policy → Asset → Action → Evidence → Review → Outcome → Score → Learning
```

Sherlock does not replace evidence receipts or policy decisions. It makes governed work discoverable, traceable, and explainable.

## Contract files

- `schemas/orggov-search-packet.v0.1.schema.json`
- `examples/orggov/search-packet.v0.1.example.json`
- `scripts/validate_orggov_search_packet.py`

## Search behavior

The v0 packet supports:

- direct lookup by workroom, work order, actor, policy decision, evidence, outcome, or scorecard;
- graph-guided tracing from work order to policy decision to action to evidence to outcome;
- ranking hints that boost authoritative evidence and policy decisions while penalizing drafts;
- clean separation between evidence references and free-text summaries.

## Invariants

- Evidence references must be non-empty.
- At least one search document must be present.
- Search document evidence weights must be normalized to 0.0 through 1.0.
- Provenance must be non-secret for committed fixtures.
- Raw prompts, secrets, credentials, or private source material do not belong in search packets.

## Cross-repo links

- Parent: `SocioProphet/prophet-platform#406`
- Sherlock workstream: `SocioProphet/sherlock-search#36`
- Policy decision: `SocioProphet/policy-fabric#57`
- AgentPlane evidence binding: `SocioProphet/agentplane#104`
- Scorecard: `SocioProphet/delivery-excellence#14`
