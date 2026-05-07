# search.backend.lexical — Contract Only

This package defines contracts for a lexical indexing/search backend capability:
- triRPC service surface (rpc/lexical.index.v0.yaml)
- topic taxonomy for event bus integration (topics/*.yaml)
- JSON Schemas for payload validation (schemas/*.json)
- a local validator (tools/validate_package.py)

## Non-goals
This package does **not** ship any runtime implementation.
Implementations live in separate packages and MUST:
1) enforce a policy guard (default deny)
2) emit governance evidence events
3) speak triRPC for all method surfaces

This sibling contract is intended to be composed underneath higher-level surfaces such as `semantic.search`.
