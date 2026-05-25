# Citance Claim Candidate v0

Status: guarded research-candidate carrier.

## Purpose

This carrier captures citance-derived scientific claim candidates for the CHRONOS Evidence Loop evidence lane.

The immediate seed is the high-value Whitbrock-adjacent candidate surfaced from a pasted search-result snippet:

```text
Echoes of Citations: Automated Extraction of Claims from Full Scientific Papers
NÖ Tan, N Tandon, O Tafjord, M Whitbrock, P Clark, et al.
AAAI 2026 candidate / unverified
```

## Boundary

Citance-derived claims are candidates, not truth.

Unverified literature candidates must remain:

```text
source_status: unverified_literature_candidate
source_quality: plausible_needs_source
implementation_safe: false
claim_status: research_only
```

A candidate may not be promoted until durable metadata and, where needed, the PDF are verified.

## Carrier surface

```text
schemas/citance-claim-candidate.v0.schema.json
fixtures/citance-claim-candidate/valid.whitbrock-echoes-citations.unverified.json
fixtures/citance-claim-candidate/invalid.unverified-implementation-safe.json
tools/validate_citance_claim_candidate.py
```

## Validation

Run:

```bash
make citance-claim-candidate-validate
```

This target is included in:

```bash
make validate
```

## Next step

Verify the paper metadata/PDF. If verified, add a confirmed fixture that preserves citance-derived claims as candidates until Holmes/Ontogenesis/Policy review admits them into a stronger carrier class.
