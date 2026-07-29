from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .ro import make_ro


@dataclass(frozen=True)
class BacklinkRow:
    source_url: str
    source_domain: str
    target_url: str
    anchor: str
    nofollow: bool
    toxic_score: float
    first_seen: str
    last_seen: str
    title: str


_LINKSELL_PAT = re.compile(r"aged domains|buy.*backlinks|backlink agency|premium backlinks", re.I)
_REPORT_PAT = re.compile(r"domain report|url shared|website stats|web directory", re.I)


def _to_bool(v: str) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def _classify(row: BacklinkRow) -> str:
    t = row.title or ""
    d = row.source_domain or ""
    if _LINKSELL_PAT.search(t) or "rankvance" in d or "prolink" in t.lower():
        return "link_seller_or_agency"
    if _REPORT_PAT.search(t) or d.endswith(".pages.dev"):
        return "auto_report_or_directory"
    if any(x in d for x in ["medium.com", "substack.com", "gitlab.com", "github.com"]):
        return "publisher_or_code_platform"
    return "other"


def _tox_band(score: float) -> str:
    # simple v0 banding
    if score >= 75:
        return "toxic"
    if score >= 45:
        return "potentially_toxic"
    return "non_toxic"


def audit_backlinks(csv_path: Path) -> dict:
    rows: list[BacklinkRow] = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for d in r:
            try:
                rows.append(
                    BacklinkRow(
                        source_url=d.get("Source URL", "") or "",
                        source_domain=d.get("Source Domain", "") or "",
                        target_url=d.get("Target URL", "") or "",
                        anchor=d.get("Anchor", "") or "",
                        nofollow=_to_bool(d.get("No Follow", "false") or "false"),
                        toxic_score=float(d.get("Toxic Score", "0") or 0.0),
                        first_seen=d.get("First Seen", "") or "",
                        last_seen=d.get("Last Seen", "") or "",
                        title=d.get("Source Page Title", "") or "",
                    )
                )
            except Exception:
                continue

    by_domain: dict[str, list[BacklinkRow]] = defaultdict(list)
    for row in rows:
        by_domain[row.source_domain].append(row)

    domain_stats = []
    bands = Counter()
    classes = Counter()
    anchors = Counter()
    follow = Counter()

    for dom, lst in by_domain.items():
        scores = [x.toxic_score for x in lst]
        mean = sum(scores) / max(1, len(scores))
        band = _tox_band(mean)
        bands[band] += 1

        cls = _classify(lst[0])
        classes[cls] += 1

        for x in lst:
            anchors[x.anchor.strip() or "(empty)"] += 1
            follow["nofollow" if x.nofollow else "follow"] += 1

        domain_stats.append(
            {
                "domain": dom,
                "links": len(lst),
                "mean_toxic": round(mean, 2),
                "band": band,
                "class": cls,
                "examples": [lst[0].source_url],
            }
        )

    domain_stats.sort(key=lambda x: (-x["mean_toxic"], -x["links"], x["domain"]))

    # RO: cluster disavow candidates (rule-based)
    disavow_candidates = [d for d in domain_stats if d["band"] == "toxic" and d["class"] != "publisher_or_code_platform"]

    ros = []
    if disavow_candidates:
        ros.append(
            make_ro(
                ro_id="RO-BL-TOXICITY-CONTAIN",
                domain="web",
                surface_ids=["backlinks"],
                evidence={
                    "toxic_domains": len(disavow_candidates),
                    "top_examples": disavow_candidates[:10],
                },
                action="review_and_disavow_domain_cluster",
                parameters={
                    "band": "toxic",
                    "exclude_classes": ["publisher_or_code_platform"],
                },
                risk_score=0.4,
                risk_factors=["disavow_can_harm_if_misapplied"],
                guardrails=["manual_review_required", "preserve_editorial_domains"],
                validation_method="time_holdout",
                primary_metric="toxic_domain_count",
                success_criteria="decreases_over_time",
            ).to_dict()
        )

    return {
        "input": {"csv": str(csv_path)},
        "summary": {
            "rows": len(rows),
            "referring_domains": len(by_domain),
            "tox_bands": dict(bands),
            "classes": dict(classes),
            "follow_split": dict(follow),
            "top_anchors": anchors.most_common(15),
        },
        "domains": domain_stats[:200],
        "recommendations": ros,
    }
