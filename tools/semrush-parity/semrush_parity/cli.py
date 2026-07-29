from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backlink_audit import audit_backlinks
from .site_audit import audit_site


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audit", description="Site + backlink audit tooling")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_site = sub.add_parser("site", help="Run site crawl + audit")
    p_site.add_argument("--base-url", required=True, help="Base URL to crawl, e.g. https://socioprophet.com")
    p_site.add_argument("--max-pages", type=int, default=200, help="Max pages to crawl")
    p_site.add_argument("--out", default="out/site_audit.json", help="Output JSON path")

    p_back = sub.add_parser("backlinks", help="Audit backlink CSV")
    p_back.add_argument("--csv", required=True, help="Path to backlink CSV")
    p_back.add_argument("--out", default="out/backlink_audit.json", help="Output JSON path")

    args = parser.parse_args(argv)

    if args.cmd == "site":
        report = audit_site(base_url=args.base_url, max_pages=args.max_pages)
        _write_json(Path(args.out), report)
        return 0

    if args.cmd == "backlinks":
        report = audit_backlinks(Path(args.csv))
        _write_json(Path(args.out), report)
        return 0

    print("unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
