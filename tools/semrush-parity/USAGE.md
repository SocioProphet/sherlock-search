# Usage (v0)

All files in this folder are designed to be lightweight and runnable without special infrastructure.

## Install

From repo root:

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r tools/semrush-parity/requirements.txt
```

## Run a site audit

```bash
python -m tools.semrush-parity.semrush_parity.cli site --base-url https://socioprophet.com --max-pages 200 --out out/site_audit.json
```

What it does:
- crawls internal pages
- extracts title/meta/canonical, internal links, text-to-html ratio
- checks /robots.txt, /sitemap.xml, /llms.txt
- emits a report and a set of Recommendation Objects (ROs)

## Run a backlink audit

```bash
python -m tools.semrush-parity.semrush_parity.cli backlinks --csv docs/dossiers/agentic-marketing-2026-04-12/backlink-sample-89-domains.csv --out out/backlink_audit.json
```

What it does:
- ingests the sample backlink CSV
- computes a toxicity band per domain (v0 rule-based)
- clusters sources into coarse classes
- emits a disavow/containment RO (manual-review gated)

## Notes

- This is v0 scaffolding. It is intentionally transparent and reproducible rather than tuned to match any vendor’s exact scoring weights.
- Some earlier chat-upload file handles were reported as expired; the canonical narrative is preserved in Drive, with IDs in the dossier manifest.
