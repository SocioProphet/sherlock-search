from __future__ import annotations

import re
import time
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str | None
    elapsed_ms: int
    bytes: int
    html: str | None
    error: str | None
    redirect_chain: list[str]


def _is_http_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def _normalize_url(url: str) -> str:
    return url.split("#", 1)[0].strip()


def fetch_url(url: str, timeout_s: float = 20.0, user_agent: str = "sherlock-audit/0.1") -> FetchResult:
    t0 = time.time()
    chain: list[str] = []
    try:
        r = requests.get(url, timeout=timeout_s, headers={"User-Agent": user_agent}, allow_redirects=True)
        elapsed_ms = int((time.time() - t0) * 1000)
        ct = r.headers.get("Content-Type")
        html = None
        if ct and "text/html" in ct.lower():
            r.encoding = r.encoding or "utf-8"
            html = r.text

        try:
            chain = [h.url for h in (r.history or [])] + [str(r.url)]
        except Exception:
            chain = [str(r.url)]

        return FetchResult(
            url=url,
            final_url=str(r.url),
            status_code=int(r.status_code),
            content_type=ct,
            elapsed_ms=elapsed_ms,
            bytes=len(r.content or b""),
            html=html,
            error=None,
            redirect_chain=chain,
        )
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            content_type=None,
            elapsed_ms=elapsed_ms,
            bytes=0,
            html=None,
            error=repr(e),
            redirect_chain=chain,
        )


def extract_links(html: str, base_url: str) -> tuple[list[dict], list[str]]:
    soup = BeautifulSoup(html, "html.parser")

    base_host = urlparse(base_url).netloc
    links: list[dict] = []
    internal: list[str] = []

    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        href = _normalize_url(urljoin(base_url, href))
        if not _is_http_url(href):
            continue
        rel = " ".join(a.get("rel") or [])
        anchor_text = unescape(re.sub(r"\s+", " ", a.get_text(" ", strip=True) or ""))
        links.append({"href": href, "anchor_text": anchor_text, "rel": rel})
        if urlparse(href).netloc == base_host:
            internal.append(href)

    return links, internal


def extract_page_fields(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")

    def _meta(name: str) -> str:
        tag = soup.find("meta", attrs={"name": name})
        return (tag.get("content") or "").strip() if tag else ""

    canonical = ""
    can = soup.find("link", rel=lambda v: v and "canonical" in str(v).lower())
    if can and can.get("href"):
        canonical = _normalize_url(urljoin(base_url, can.get("href")))

    robots = ""
    mrobots = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if mrobots and mrobots.get("content"):
        robots = (mrobots.get("content") or "").strip()

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True) or "")

    html_len = len(html)
    text_len = len(text)
    text_to_html = (text_len / html_len) if html_len else 0.0
    word_count = len([w for w in text.split(" ") if w])

    links, internal = extract_links(html, base_url)
    no_anchor = sum(1 for l in links if not (l.get("anchor_text") or "").strip())

    return {
        "title": title,
        "meta_description": _meta("description"),
        "canonical": canonical,
        "meta_robots": robots,
        "text": text,
        "word_count": word_count,
        "text_to_html_ratio": text_to_html,
        "links": links,
        "internal_urls": internal,
        "links_no_anchor_text": no_anchor,
    }


def crawl_site(base_url: str, max_pages: int = 200, timeout_s: float = 20.0) -> dict:
    base_url = base_url.rstrip("/") + "/"
    base_host = urlparse(base_url).netloc

    queue: list[str] = [base_url]
    seen: set[str] = set()

    pages: dict[str, dict] = {}
    edges: list[dict] = []

    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        url = _normalize_url(url)
        if url in seen:
            continue
        if urlparse(url).netloc != base_host:
            continue

        seen.add(url)
        fr = fetch_url(url, timeout_s=timeout_s)
        rec = {"fetch": fr.__dict__}

        if fr.html:
            fields = extract_page_fields(fr.html, url)
            rec["extract"] = {
                k: v
                for k, v in fields.items()
                if k not in {"links", "internal_urls"}  # keep: includes text for near-dup
            }

            for link in fields["links"]:
                dst = link["href"]
                if urlparse(dst).netloc == base_host:
                    edges.append(
                        {
                            "src": url,
                            "dst": dst,
                            "anchor_text": link.get("anchor_text", ""),
                            "rel": link.get("rel", ""),
                        }
                    )

            for u in fields["internal_urls"]:
                if u not in seen and len(queue) < max_pages * 5:
                    queue.append(u)

        pages[url] = rec

    return {
        "base_url": base_url,
        "max_pages": max_pages,
        "pages": pages,
        "edges": edges,
        "stats": {"crawled": len(pages), "edges": len(edges)},
    }
