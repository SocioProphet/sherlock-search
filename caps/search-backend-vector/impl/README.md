# search-backend-vector → HellGraph

This implements the `search-backend-vector` capability over **HellGraph** (`@socioprophet/hellgraph`),
so Sherlock's vector retrieval lane and the Noetica/SourceOS brain are **one atomspace**: a vector
candidate Sherlock proposes is anchored in the same graph the agent reasons over.

## What it does
- `vectorUpsert(req)` → stores the document's embedding as a HellGraph `DocumentChunk` atom
  (idempotent per `doc_id`). Honours `schemas/vector_upsert.schema.json`.
- `vectorQuery(req)` → cosine-scores the query vector over every embedded chunk and returns the
  `top_k` as `{ doc_id, score, distance }`. Honours `schemas/vector_query{,_response}.schema.json`.
- Every op emits an `EvidenceEvent` (`schemas/evidence_event.schema.json`) with `decision:
  allow|deny|error` for Sherlock's governed evidence lane.

## Governance boundary (unchanged)
This backend only does **vector retrieval** — it produces `candidate_only` material. Per the
evidence-answer contract (`docs/evidence-answer-contract.md`), a vector candidate stays provisional
until **Holmes** verifies (`explanationTrace`) and **Policy Fabric** admits (`policyDecision`).
HellGraph is the substrate Sherlock anchors against; it is *not* an admission authority. This is the
same propose → verify → promote shape used across the platform.

## Run the smoke
```bash
# hermetic: throwaway HOME so the default atomspace never touches the primary brain
HOME=$(mktemp -d) bun caps/search-backend-vector/impl/smoke_hellgraph_backend.ts
```
Expected: three upserts, a paraphrase query that ranks `doc:retry` first, and a response that
validates against `schemas/vector_query_response.schema.json`. Requires a local Ollama
(`nomic-embed-text`) for the smoke's embeddings; the backend itself is embed-agnostic (callers pass
vectors in).

## Wiring
`package.json` declares `@socioprophet/hellgraph` (`file:../hellgraph`). The Sherlock service mounts
`vectorUpsert`/`vectorQuery` behind the cap's RPC (`rpc/vector.index.v0.yaml`) and drains
`evidenceEvents()` onto its evidence lane.
