# Source Quality Answer Trace v0

Status: v0.1 bounded contract surface.

This document defines the Sherlock-side source-quality answer trace carrier for the Watson/Cyc/Semantic-Web/CHRONOS deployable loop.

## Purpose

Sherlock owns the evidence discovery and answer-trace boundary. This contract lets Sherlock emit a local, source-quality-aware answer trace that downstream systems can consume without treating every retrieved record as implementation-grade evidence.

The intended integration path is:

```text
Sherlock source-quality answer trace
  -> Ontogenesis corpus event semantics
  -> Policy Fabric policy decision
  -> Agentplane bounded action proposal
  -> Model Governance Ledger audit event
```

## Added surfaces

```text
schemas/source-quality-answer-trace.v0.schema.json
fixtures/source-quality-answer-trace/valid.confirmed-bibliographic.json
fixtures/source-quality-answer-trace/invalid.claim-without-evidence.json
fixtures/source-quality-answer-trace/invalid.source-missing-quality.json
fixtures/source-quality-answer-trace/invalid.research-only-marked-implementation-safe.json
tools/validate_source_quality_answer_trace.py
```

## Source quality vocabulary

```text
confirmed_official
confirmed_bibliographic
confirmed_pdf
confirmed_artifact
plausible_needs_source
speculative_do_not_use
```

Only confirmed source qualities may support an `implementation_safe` answer trace. `plausible_needs_source` and `speculative_do_not_use` remain research-only.

## Validation behavior

The validator checks:

- JSON Schema shape;
- source-quality presence;
- claims reference known sources;
- answer traces reference known claims and sources;
- diagnostic findings reference known sources;
- research-only source qualities cannot produce implementation-safe traces.

Run:

```bash
make source-quality-answer-trace-validate
```

The target is also included in:

```bash
make validate
```

## Boundary

This contract does not implement:

- external search;
- bibliography harvesting;
- GraphRAG;
- vector indexing;
- model calls;
- Holmes verification;
- Policy Fabric admission;
- Agentplane execution.

It is a local contract, fixture, and validation surface only.
