# Sherlock Query Plane and Matrix ChatOps Architecture

## Purpose

`sherlock-search` is the canonical search and discovery plane for governed support, premium support, operational intelligence, asset reuse, and evidence-backed self-service across the SocioProphet repository universe.

Sherlock is not just a keyword search service. It is the query and retrieval orchestration layer that can be invoked from web/runtime surfaces, internal operator tools, support and premium-support agents, Matrix chatops rooms and workflows, evaluation and replay tools, and future self-service workflows across platform, knowledge, and learning lanes.

## Core design rules

1. Ontology first. Query targets, result classes, filters, and citations must be grounded in canonical semantic classes from `ontogenesis`.
2. Typed interfaces first. Query requests, plans, results, citations, evidence bundles, and action suggestions must use typed contracts.
3. No direct raw-telemetry reasoning. Sherlock may surface operational context, but logs, anomalies, metering, incidents, ticket clusters, and explainability traces must be normalized through `global-devsecops-intelligence` before they are returned or acted on.
4. Support-tier aware retrieval. Standard support, premium support, and mission-critical support may share the same query plane while differing in entitlement, overlays, disclosure boundary, and recommendation authority.
5. Evidence-bearing answers. Sherlock responses should carry citations, provenance references, policy boundary flags, and when relevant, replay or evidence handles.

## Matrix ChatOps role

Sherlock will also operate as a Matrix chatops agent.

This requires room-scoped query handling, identity and entitlement-aware retrieval, support and premium-support workflows in chat, incident, anomaly, and metering explainability in chat, command-style and natural-language query entry, escalation packet generation, evidence and citation summaries suitable for operator rooms, and follow-on action suggestions that can be handed to `agentplane` for bounded execution.

## Query planes and sources

Sherlock should treat these as distinct but composable query planes.

### Asset and template plane
Reusable support assets, content blocks, templates, runbooks, trust statements, evaluation kits, and reusable response components.

### Operational intelligence plane
Logs, anomalies, metering, service health, incident stories, ticket groupings, explainability packages, and operational evidence from `global-devsecops-intelligence`.

### Memory plane
Prior interactions, prior decisions, historical support outcomes, accepted or rejected recommendations, customer overlays, and prior promotions from `memory-mesh`.

### Learning plane
Curriculum objects, explanation quality objectives, support pedagogic patterns, and guided remediation and education assets from `alexandrian-academy`.

### Execution and evidence plane
Bounded diagnostics, remediation bundles, replay artifacts, validation outputs, and execution receipts from `agentplane` and `prophet-platform`.

## Typed interfaces

The minimum interface family Sherlock should speak includes `QueryRequest`, `QueryPlan`, `QueryResultSet`, `ActionSuggestion`, and `EscalationPacket`.

## Standard support vs premium support

Sherlock should use one base retrieval and orchestration system with tier-aware overlays.

Standard support uses the shared canonical asset graph, standard memory scopes, bounded retrieval and recommendation rights, generic anomaly and metering views, and generic runbooks and escalation options.

Premium support uses tenant/account overlays, deeper memory scopes and prior-case recall, premium-specific asset overlays, customized anomaly thresholds and service groupings sourced from `global-devsecops-intelligence`, higher-grade recommendation and escalation rights, and TAM/SME-oriented summary and handoff support.

## Repository integration map

- `ontogenesis`: semantic classes and policy-backed query meaning
- `socioprophet-standards-storage`: base transport, storage, and interface invariants
- `global-devsecops-intelligence`: ops-domain processing for logs, anomalies, metering, stories, and explainability
- `memory-mesh`: long-horizon recall and prior decision memory
- `meshrush`: fast adaptive observation pressure and short-horizon recommendation pressure
- `alexandrian-academy`: learning-objective and pedagogic quality inputs
- `agentplane`: bounded execution and replayable action handoff
- `prophet-platform`: runtime/eval services and query hosting
- `sociosphere`: deterministic workspace materialization and repo composition

## Immediate tranche

1. Land this architectural contract in `sherlock-search`.
2. Define typed query contracts and ontology bindings in upstream standards/ontology repos.
3. Integrate Sherlock with the ops-domain processing semantics in `global-devsecops-intelligence`.
4. Add Matrix chatops adapter contracts and room safety rules.

## Outcome

When implemented correctly, Sherlock becomes the governed, queryable search-and-discovery spine for support, premium support, Matrix chatops, operational intelligence lookup, reusable content and asset retrieval, memory-backed explanation, and evidence-bearing next-best-action guidance.
