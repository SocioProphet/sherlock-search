"""sherlock_audit

Canonical audit + parity tooling for:
- site audit (crawl + issue detectors)
- backlink audit (CSV + later GSC/CommonCrawl ingestion)
- Recommendation Object emission

This package was created to replace the earlier `tools/semrush-parity/` scaffold, which is not
import-safe due to the hyphen in the folder name.
"""

__all__ = [
    "cli",
    "crawl",
    "site_audit",
    "backlink_audit",
    "metrics",
    "ro",
    "render",
]
