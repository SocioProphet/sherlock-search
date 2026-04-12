"""Audit tooling scaffold.

Note: folder name retained for continuity with earlier notes, but the code itself is generic:
- site audit via crawling + issue detectors
- backlink audit via inbound link CSV ingestion + rule-based toxicity v0
- Recommendation Object emission

All outputs are intended to be reproducible and versioned.
"""

__all__ = [
  "cli",
  "crawl",
  "site_audit",
  "backlink_audit",
  "ro",
  "metrics",
]
