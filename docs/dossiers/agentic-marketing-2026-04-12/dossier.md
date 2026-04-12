# Full Dossier: Agentic Marketing, Prospecting, Discovery, Surfaces, Bias, Curvature, and Capability-Parity

Comprehensive resynthesis of the entire chat, including all major frameworks, datasets, artifacts, formulas, analyses, and open work. Generated 2026-04-04 14:30 UTC.


# Purpose, provenance, and scope

This dossier is a full archival resynthesis of the conversation. It preserves the original problem statement, every major conceptual pivot, every artifact created during the session, the intermediate work products, the decisions made, and the remaining backlog.

Goals:
- Preserve the work so it can be replayed, audited, and continued.
- Provide an operationally usable framework, not just narrative.
- Enable repository/Drive integration with clear inventories and pointers.

Primary sources explicitly used in the work:
- MeshRush Omni (omnichannel discovery, feasibility gating, bias-aware measurement, Recommendation Objects).
- “Wisdom built her house…” (hyperbolic curvature framing, entropy-curvature coupling, lawful ledger).
- Semrush Site Audit and Backlink Audit reports for socioprophet.com (Mar 4, 2026).
- User-provided backlink sample (89 domains) extracted into a labeled dataset.


# Core framing: channel vs surface vs property

We treat:
- Channel as distribution mechanism.
- Property as a publisher/platform destination.
- Surface as the actionable inventory/context inside a property.

We emphasize: pricing and sampling behaviors are surface properties more than channel properties.


# Personas -> tags -> distributions

We started with four personas and then generalized:
- Personas are narrative bundles.
- Atomic tags are operational primitives.
- Targeting and sampling are distributions over tags.

The central analytic move is to track the target distribution T and the observed distribution P_{s,t} per surface s over time window t.


# Pricing dynamics vs sampling dynamics

We separated:
- Pricing: why inventory costs what it costs.
- Sampling: who we actually reach and how that differs from the target population.

We treated annual developer surveys as hybrid structures: attention events + sampling frames + publishing moments.


# Bias-based metrics (skew) and curvature

We defined:
- JS distance / TV distance of observed distributions vs target (alignment) and vs population baseline (novelty).
- Drift/volatility/persistence across windows.

We then formalized the curvature hypothesis as second-order sensitivity:
- Let r be distance to mean-field; let E be an engagement/action metric.
- Curvature κ ≈ ∂² E[E|r] / ∂r².

Operational indices:
- ABA = D_pop × (1 - D_tgt).
- CWAP = norm(E) × norm(D_pop) × norm(|κ|).
- NetPriority = CWAP × (1 - Risk).


# Bias correction (friendship paradox / degree-biased sampling)

We adopted MeshRush’s inverse-degree weighting pattern to correct degree-biased samples.
We required recording sampling_mode for every measurement.


# CLAD: Curvature-Aware, Lawful, Agentic Discovery

We synthesized a closed-loop operating model:
1) Sense (telemetry)
2) Feasibility + policy gating
3) Embed (semantic + optional hyperbolic)
4) Diagnose bias + skew
5) Estimate curvature + knees
6) Recommend (ROs)
7) Experiment (holdouts)
8) Stabilize (operate away from cliffs; schedule entropy)
9) Ledger (forensic replay)


# SocioProphet websurface integration

We aligned targeting and measurement to “domain surfaces” with purpose, privilege boundaries, and routing policies.
We proposed a Surface Registry as a canonical substrate.


# Semrush grounding (Mar 4, 2026)

Site audit highlights (socioprophet.com):
- Site Health 77%, AI Search Health 86%
- 61 crawled; 24 redirects; 30 with issues; 7 broken; 0 healthy
- 30 duplicate titles; 30 duplicate meta; 30 duplicate content
- 4 pages returning 4XX; 2 DNS crawl failures
- robots.txt and sitemap.xml missing (404)
- llms.txt missing
- internal link graph issues (18 pages with only 1 incoming link)

Backlink audit highlights:
- Overall Toxic Score: MEDIUM
- 89 referring domains; 120 analyzed backlinks
- 37 toxic, 17 potentially toxic, 35 non-toxic
- Anchor distribution dominated by socioprophet.com


# Backlink sample analysis

We analyzed the 89-domain sample:
- Many link-seller/auto-generated directory/report domains with high toxicity and churn.
- Treated as risk surfaces (containment/cleanup), not candidate marketing channels.


# Capability parity blueprint (Semrush-style reports)

We defined parity tiers:
- Tier A: site audit parity (first-party crawl; high parity)
- Tier B: backlink parity in shape (coverage differs)
- Tier C: Semrush-scale competitive link intelligence (requires planet-scale crawling)

We specified datasets:
- Site: crawl_run, fetch, page_extract, page_text, internal_link_edges, issue
- Backlink: inbound_link_edges, domain_features, toxicity_scores

We specified open-source tooling:
- Scrapy + Playwright; trafilatura/readability; lxml/BS4
- Postgres/ClickHouse/DuckDB; dbt
- networkx; MinHash/SimHash
- Dagster/Airflow; OpenTelemetry


# Artifact inventory

Key generated workbooks and templates:
- persona_top_100_properties.xlsx
- media_universe_personas_top100.xlsx
- media_universe_with_bias_metrics_template.xlsx
- audience_tagging_framework_template.xlsx
- agentic_marketing_resynthesis_plan*.xlsx
- semrush_capability_parity_blueprint.xlsx

Source PDFs:
- MeshRush Omni
- Wisdom/curvature PDF
- Semrush Site Audit
- Semrush Backlink Audit


# Backlog (condensed)

- Build Surface Registry (domains + path patterns + privilege boundaries + intent).
- Implement site crawl + detectors for Semrush parity.
- Implement backlink ingestion (GSC + CommonCrawl + targeted refetch) + toxicity model v0.
- Implement RO engine + validation harness.
- Implement lawful ledger (hash chain) for replay and audit.
- Implement curvature/knee estimators with sample-size guards and bias correction.


# Operational analysis report

Inputs/Scope & Trust Boundaries
- Inputs: chat, PDFs, Semrush outputs, backlink sample, generated workbooks.
- Boundaries: privilege boundaries for surfaces; trust gating for toxic link ecosystems.

Method/Evidence Extraction
- Extracted Semrush issue counts and converted into RO packs.
- Created bias/skew/curvature metrics and calibration plans.

Validation & Consistency Checks
- Bias correction required to avoid curvature hallucinations.
- Parity claims separated by coverage tier.

Artifacts & Repo Destinations
- Drive: authoritative Docs (IDs in manifest).
- Repo: versioned dossier + schemas + sample datasets.

Decision Log
- Personas → tags.
- Surfaces as unit of action.
- Feasibility gate before ranking.
- Curvature as sensitivity; tested not assumed.

Gaps & Unknowns
- Full backlink universe not ingested (sample only).
- Semrush weightings proprietary.

Risk Register Delta
- Added risk gating to prevent optimizing into outrage/spam.

Next Two Steps
1) Merge this dossier branch into main after review.
2) Start the Semrush-parity tooling scaffold (crawler + detectors + RO engine) in this repo.
