# Sherlock Evidence-Answer Contract (Anchor -> Normalize -> Propose)

This document defines Sherlock-side contracts for evidence-governed answers under the SocioProphet reference architecture.

## Ownership boundary

Sherlock owns:

- query parsing
- entity/relation candidate extraction
- anchor construction
- evidence retrieval/ranking/normalization
- proposed-claim planning
- display of explanation and policy status

Sherlock does not own:

- Holmes proof/verification logic
- Policy Fabric admission/denial decisions
- conversion of vector candidates into admitted claims

## Canonical query pipeline

`parse -> entity/relation candidates -> anchors/evidence -> proposed claims -> Holmes verification -> policy status -> answer display`

The broader loop remains:

`Observe -> Anchor -> Normalize -> Propose -> Explain -> Verify -> Govern -> Act -> Receipt -> Learn`

Sherlock is responsible for the `Anchor -> Normalize -> Propose` segment and handoff.

## Required objects

- `Anchor`: immutable reference to a source location used to ground retrieval and citation.
- `Evidence`: ranked retrieval unit bound to one or more anchors, with support/opposition/freshness metadata.
- `Claim` (proposed claim): candidate answer statement emitted by Sherlock before Holmes/Policy admission.
- `VectorCandidate`: vector retrieval output with `status: candidate_only` until downstream verification/admission.
- `ExplanationTrace`: Holmes-supplied verification trace/status shown by Sherlock.
- `PolicyDecision`: Policy/Guardrail Fabric decision/status shown by Sherlock.

## Display contract notes

Answer rendering must keep these lanes visible:

1. supporting evidence
2. opposing or stale evidence
3. Holmes explanation trace/status
4. confidence + truth bounds
5. policy status (pending/allowed/denied)

## Fixtures and validation note

Deterministic fixtures:

- `fixtures/evidence-answer-contract/technical-document-answer.sherlock-contract.json`
- `fixtures/evidence-answer-contract/vector-candidate.sherlock-contract.json`

Required fields enforced by validator:

- technical document fixture: `query`, `anchors[]`, `evidence[]`, `proposedClaims[]`, `explanationTrace`, `policyDecision`
- vector fixture: `query`, `evidence[]`, `vectorCandidates[]`, `explanationTrace`, `policyDecision`
- each `vectorCandidates[]` item must include role-level match metadata and `status: candidate_only`

Validate locally:

```bash
python tools/validate_evidence_answer_contract_fixture.py
```

## Cross-repo handoff notes

- Holmes consumes proposed claims + evidence refs and returns `ExplanationTrace`.
- Policy Fabric consumes verification context and returns `PolicyDecision`.
- Sociosphere, GAIA, and Agentplane consume Sherlock’s contract boundary for query/evidence/answer handoffs and display-state interoperability.
