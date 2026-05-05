# Prophet Understand Search Lane

## Purpose

Sherlock Search is the hybrid query membrane over Prophet Understand / Repo Intelligence v0 artifacts.

The v0 flow is:

1. Smart Tree emits `.prophet/prophet-understanding.json`.
2. Lampstand indexes the artifact into deterministic records.
3. Sherlock ranks and explains those records for humans and agents.

## Query contract

Sherlock consumes records with these minimum fields:

- `repo_full_name`
- `repo_commit`
- `schema_version`
- `record_family`
- `record_id`
- `title`
- `text`
- `node_id` / `edge_id` where present
- `path` where present
- `source_anchor` where present
- `confidence` where present
- `provenance_receipt_ids`
- `policy_state`
- `validation_status` where present
- `raw`

## Ranking stance

v0 ranking is evidence-first and must not pretend to be deeper than the available index. The initial ranker may combine:

- lexical term overlap
- title boost
- path boost
- graph record family boost
- confidence boost
- policy/validation penalty
- exact node or path match boost

Semantic/vector ranking is allowed only when an embedding field or retrieval backend is explicitly present. Until then, Sherlock must label the lane as lexical/graph/evidence search, not as proven semantic search.

## Required answer shape

A search result should return:

- answer summary
- ranked records
- graph path explanation when edge records are present
- source anchor where present
- provenance receipt IDs
- policy state
- validation status
- confidence

## Seed queries

The v0 fixture/query path should support:

- `what owns this file?`
- `what depends on this contract?`
- `which tests cover this node?`
- `what changed in this PR impact set?`
- `what policy gates touch this service?`

## Safety rules

Sherlock must preserve warnings. Invalid, stale, missing-provenance, or policy-risk records should be visible and ranked with explicit status, not silently excluded.

No answer should claim a graph fact without a record ID and provenance reference.
