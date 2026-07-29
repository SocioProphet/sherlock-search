# sherlock_audit (canonical tooling)

This is the canonical location for the **open-source audit + discovery tooling** we are building to achieve **Semrush-style capability parity** (site audit + backlink audit) while remaining:

- reproducible (deterministic-ish outputs; versioned inputs)
- bias-aware (sampling_mode + degree-proxy correction hooks)
- agentic (Recommendation Objects emitted as the actuation interface)
- auditable (designed to be ledger-compatible)

## Why this folder exists

Earlier in the session we created a first-pass scaffold under `tools/semrush-parity/`. That path is not import-safe in Python because of the hyphen. This folder is the corrected, runnable implementation.

## What is included (v0)

- `sherlock_audit/` python package with:
  - `crawl.py`: crawler + extraction + redirect tracing
  - `site_audit.py`: issue detectors + health score v0 + RO emission
  - `backlink_audit.py`: backlink CSV ingestion + toxicity v0 + RO emission
  - `metrics.py`: distribution distance helpers (TV + JS)
  - `ro.py`: RO builder
  - `render.py`: markdown report renderer
  - `cli.py`: CLI entrypoint
- `requirements.txt`: minimal dependencies
- `USAGE.md`: copy/paste commands

## Roadmap

1) Add near-duplicate content detection (k-min sketch / minhash) and redirect-chain reports (implemented in v0.1).
2) Add Search Console and Common Crawl ingestion for backlink coverage.
3) Add RO execution harness + validation loop.
4) Add hash-ledger outputs for forensic replay.
