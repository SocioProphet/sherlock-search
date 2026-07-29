from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from urllib.parse import urljoin, urlparse

from .crawl import crawl_site, fetch_url
from .ro import make_ro


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def _dup_counts(values: list[str]) -> dict[str, int]:
    c = Counter([v.strip() for v in values if v and v.strip()])
    return {k: v for k, v in c.items() if v >= 2}


def _classify_status(status: int) -> str:
    if status == 0:
        return "error"
    if 200 <= status < 300:
        return "ok"
    if 300 <= status < 400:
        return "redirect"
    if 400 <= status < 500:
        return "4xx"
    if status >= 500:
        return "5xx"
    return "other"


def audit_site(base_url: str, max_pages: int = 200) -> dict:
    base_url = base_url.rstrip("/") + "/"
    host = urlparse(base_url).netloc

    crawl = crawl_site(base_url, max_pages=max_pages)

    pages = crawl["pages"]
    edges = crawl["edges"]

    # status buckets
    buckets = Counter()
    redirects = []
    broken = []
    dns_or_fetch_errors = []

    titles: list[str] = []
    metas: list[str] = []
    canonicals: list[str] = []

    page_title_by_url: dict[str, str] = {}
    meta_by_url: dict[str, str] = {}

    links_no_anchor_total = 0

    for url, rec in pages.items():
        fr = rec.get("fetch", {})
        status = int(fr.get("status_code") or 0)
        cls = _classify_status(status)
        buckets[cls] += 1

        if cls == "redirect":
            redirects.append({"url": url, "final_url": fr.get("final_url")})
        if cls in {"4xx", "5xx"}:
            broken.append({"url": url, "status": status, "final_url": fr.get("final_url")})
        if cls == "error":
            dns_or_fetch_errors.append({"url": url, "error": fr.get("error")})

        ex = rec.get("extract") or {}
        title = ex.get("title", "")
        meta = ex.get("meta_description", "")
        canonical = ex.get("canonical", "")

        page_title_by_url[url] = title
        meta_by_url[url] = meta

        titles.append(title)
        metas.append(meta)
        canonicals.append(canonical)

        links_no_anchor_total += int(ex.get("links_no_anchor_text") or 0)

    # internal link indegree
    indegree = Counter()
    for e in edges:
        indegree[e["dst"]] += 1

    low_incoming = [u for u in pages.keys() if indegree.get(u, 0) <= 1]

    # duplicates (exact)
    dup_titles = _dup_counts(titles)
    dup_metas = _dup_counts(metas)

    # canonical inconsistencies
    missing_canonical = [u for u, c in zip(pages.keys(), canonicals) if not (c or "").strip()]

    # root files
    robots = fetch_url(urljoin(base_url, "/robots.txt"))
    sitemap = fetch_url(urljoin(base_url, "/sitemap.xml"))
    llms = fetch_url(urljoin(base_url, "/llms.txt"))

    issues: list[dict] = []
    ros: list[dict] = []

    def add_issue(code: str, severity: str, evidence: dict) -> None:
        issues.append({"code": code, "severity": severity, "evidence": evidence})

    if robots.status_code == 404:
        add_issue("missing_robots_txt", "error", {"url": robots.url, "status": robots.status_code})
        ros.append(
            make_ro(
                ro_id="RO-SEO-ROBOTS",
                domain="web",
                surface_ids=[base_url],
                evidence={"issue": "missing_robots_txt"},
                action="add_robots_txt",
                parameters={"path": "/robots.txt"},
                risk_score=0.15,
                validation_method="time_holdout",
                primary_metric="missing_robots_txt",
                success_criteria="resolved",
            ).to_dict()
        )

    if sitemap.status_code == 404:
        add_issue("missing_sitemap_xml", "error", {"url": sitemap.url, "status": sitemap.status_code})
        ros.append(
            make_ro(
                ro_id="RO-SEO-SITEMAP",
                domain="web",
                surface_ids=[base_url],
                evidence={"issue": "missing_sitemap_xml"},
                action="add_sitemap_xml",
                parameters={"path": "/sitemap.xml"},
                risk_score=0.2,
                validation_method="time_holdout",
                primary_metric="missing_sitemap_xml",
                success_criteria="resolved",
            ).to_dict()
        )

    if llms.status_code in {0, 404}:
        add_issue("missing_llms_txt", "notice", {"url": llms.url, "status": llms.status_code})
        ros.append(
            make_ro(
                ro_id="RO-AI-LLMS",
                domain="web",
                surface_ids=[base_url],
                evidence={"issue": "missing_llms_txt"},
                action="add_llms_txt",
                parameters={"path": "/llms.txt"},
                risk_score=0.05,
                validation_method="time_holdout",
                primary_metric="missing_llms_txt",
                success_criteria="resolved",
            ).to_dict()
        )

    if dup_titles:
        add_issue("duplicate_title", "warning", {"count": len(dup_titles), "examples": list(dup_titles)[:10]})
        ros.append(
            make_ro(
                ro_id="RO-SEO-DUP-TITLE",
                domain="web",
                surface_ids=[base_url],
                evidence={"issue": "duplicate_title", "duplicate_values": list(dup_titles)[:20]},
                action="dedupe_titles",
                parameters={"strategy": "template_unique_titles"},
                risk_score=0.25,
                validation_method="time_holdout",
                primary_metric="duplicate_title",
                success_criteria="count_decreases",
            ).to_dict()
        )

    if dup_metas:
        add_issue("duplicate_meta_description", "warning", {"count": len(dup_metas), "examples": list(dup_metas)[:10]})

    if broken:
        add_issue("broken_pages", "error", {"count": len(broken), "examples": broken[:10]})

    if dns_or_fetch_errors:
        add_issue("fetch_errors", "error", {"count": len(dns_or_fetch_errors), "examples": dns_or_fetch_errors[:10]})

    if low_incoming:
        add_issue("low_internal_incoming_links", "notice", {"count": len(low_incoming), "examples": low_incoming[:15]})

    if links_no_anchor_total:
        add_issue("links_missing_anchor_text", "notice", {"count": links_no_anchor_total})

    if missing_canonical:
        add_issue("missing_canonical", "notice", {"count": len(missing_canonical), "examples": missing_canonical[:10]})

    # health score (transparent, not Semrush weights)
    # errors weigh more than warnings; notices small.
    weights = {"error": 5.0, "warning": 2.0, "notice": 0.5}
    affected = defaultdict(int)
    for it in issues:
        affected[it["severity"]] += 1
    denom = max(1, len(pages))
    penalty = sum(weights[s] * (affected[s] / denom) for s in affected)
    health = max(0.0, min(100.0, 100.0 - 20.0 * penalty))

    return {
        "input": {"base_url": base_url, "max_pages": max_pages},
        "crawl": {
            "crawled": crawl["stats"]["crawled"],
            "edges": crawl["stats"]["edges"],
            "buckets": dict(buckets),
        },
        "derived": {
            "redirects": redirects[:50],
            "broken": broken[:50],
            "fetch_errors": dns_or_fetch_errors[:50],
            "low_incoming_internal": low_incoming[:200],
            "duplicate_title_values": list(dup_titles)[:50],
            "duplicate_meta_values": list(dup_metas)[:50],
            "links_no_anchor_text_total": links_no_anchor_total,
        },
        "issues": issues,
        "recommendations": ros,
        "scores": {
            "site_health_v0": round(health, 2),
        },
        "provenance": {
            "crawl_hash": _sha1(str(sorted(pages.keys()))),
        },
    }
