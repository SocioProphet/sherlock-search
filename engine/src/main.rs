// Sherlock engine — sovereign, ontology-driven HYBRID Discovery search (no JVM).
//   lexical: Tantivy (Lucene-in-Rust, BM25)
//   dense:   estate embeddings (nomic-embed-text) → Qdrant (shared platform vector substrate)
//   fusion:  Reciprocal Rank Fusion (RRF) of the two ranked lists
// Dense tier is OPTIONAL: if EMBEDDINGS_URL / QDRANT_URL are unset or unreachable, it degrades to
// BM25-only (never fails the query). Riding the shared mesh-qdrant — not a new vector store.
use serde::Deserialize;
use serde_json::json;
use std::collections::{BTreeMap, HashMap};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;
use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::schema::{OwnedValue, Schema, FAST, STORED, STRING, TEXT};
use tantivy::{doc, Index, TantivyDocument};

#[derive(Deserialize, Clone)]
struct Doc {
    id: String,
    title: String,
    doctype: String,
    category: String,
    region: String,
    score: f64,
    body: String,
}

fn qparam(url: &str, key: &str) -> Option<String> {
    let q = url.split_once('?')?.1;
    for pair in q.split('&') {
        if let Some((k, v)) = pair.split_once('=') {
            if k == key {
                return Some(urldecode(v));
            }
        }
    }
    None
}
fn urldecode(s: &str) -> String {
    let s = s.replace('+', " ");
    let bytes = s.as_bytes();
    let mut out = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            if let Ok(b) = u8::from_str_radix(&s[i + 1..i + 3], 16) {
                out.push(b);
                i += 3;
                continue;
            }
        }
        out.push(bytes[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}
fn sanitize(q: &str) -> String {
    q.chars()
        .map(|c| if c.is_alphanumeric() || c.is_whitespace() { c } else { ' ' })
        .collect()
}
fn floor_boundary(s: &str, mut i: usize) -> usize {
    if i >= s.len() {
        return s.len();
    }
    while i > 0 && !s.is_char_boundary(i) {
        i -= 1;
    }
    i
}
// window snippet with <b> term highlights (ASCII corpus; case-insensitive)
fn highlight(body: &str, query: &str) -> String {
    let terms: Vec<String> = query
        .to_lowercase()
        .split_whitespace()
        .filter(|w| w.len() >= 4)
        .map(str::to_string)
        .collect();
    if terms.is_empty() {
        return body.chars().take(200).collect();
    }
    let lower = body.to_lowercase();
    let pos = terms.iter().filter_map(|t| lower.find(t.as_str())).min().unwrap_or(0);
    let start = floor_boundary(body, pos.saturating_sub(60));
    let end = floor_boundary(body, (start + 240).min(body.len()));
    let window = &body[start..end];
    let wl = window.to_lowercase();
    let mut out = String::new();
    let mut i = 0;
    while i < window.len() {
        let mut matched = false;
        for t in &terms {
            if i + t.len() <= wl.len() && wl[i..].starts_with(t.as_str()) {
                out.push_str("<b>");
                out.push_str(&window[i..i + t.len()]);
                out.push_str("</b>");
                i += t.len();
                matched = true;
                break;
            }
        }
        if !matched {
            let ch_len = window[i..].chars().next().map(|c| c.len_utf8()).unwrap_or(1);
            out.push_str(&window[i..i + ch_len]);
            i += ch_len;
        }
    }
    format!("{}{}{}", if start > 0 { "…" } else { "" }, out, if end < body.len() { "…" } else { "" })
}

fn embed(agent: &ureq::Agent, url: &str, model: &str, text: &str) -> Option<Vec<f32>> {
    let resp = agent.post(url).send_json(json!({ "input": text, "model": model })).ok()?;
    let v: serde_json::Value = resp.into_json().ok()?;
    let arr = v.get("data")?.get(0)?.get("embedding")?.as_array()?;
    Some(arr.iter().filter_map(|x| x.as_f64().map(|f| f as f32)).collect())
}

// ── SP-RETR-TRUTH-001: honest, request-time provenance ──────────────────────
// The retrieval label MUST reflect what the dense path actually produced THIS
// request, not the boot-time `dense` flag. If dense was configured-on but
// contributed nothing (embed failed / qdrant error / empty result), RRF over an
// empty second list is a monotone reindex of BM25 — i.e. the ordering is
// BM25-only, so the response must say so instead of claiming hybrid fusion.
struct RetrievalMode {
    engine: String,          // backward-compat string, now DERIVED FROM OUTCOME
    lexical: bool,
    dense: bool,             // did the dense path return >=1 result THIS request
    fusion: &'static str,    // "rrf_k60" only when dense actually contributed
    degraded: Option<String>, // set iff dense was configured-on but produced nothing
}

fn retrieval_mode(dense_configured: bool, dense_hits: usize, degrade_reason: Option<&str>) -> RetrievalMode {
    let contributed = dense_hits > 0;
    RetrievalMode {
        engine: if contributed { "tantivy+qdrant(rrf)".into() } else { "tantivy".into() },
        lexical: true,
        dense: contributed,
        fusion: if contributed { "rrf_k60" } else { "none" },
        degraded: if dense_configured && !contributed {
            Some(degrade_reason.unwrap_or("dense_unavailable: empty_result").to_string())
        } else {
            None
        },
    }
}

// Monotonic per-process event sequence so event_ids are unique within a run.
static EVT_SEQ: AtomicU64 = AtomicU64::new(1);

fn now_secs() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

// Dep-free RFC3339 (UTC, seconds precision) via Howard Hinnant's civil-from-days.
// Kept local so the dense-failure audit trail needs no new crate / compile cost.
fn rfc3339_utc(secs: u64) -> String {
    let days = (secs / 86_400) as i64;
    let sod = secs % 86_400;
    let (h, mi, s) = (sod / 3600, (sod % 3600) / 60, sod % 60);
    let z = days + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097; // [0, 146096]
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365; // [0, 399]
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100); // [0, 365]
    let mp = (5 * doy + 2) / 153; // [0, 11]
    let d = doy - (153 * mp + 2) / 5 + 1; // [1, 31]
    let m = if mp < 10 { mp + 3 } else { mp - 9 }; // [1, 12]
    let y = if m <= 2 { y + 1 } else { y };
    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z", y, m, d, h, mi, s)
}

// Build an EvidenceEvent conforming to caps/semantic-search-bi/schemas/evidence_event.schema.json
// (additionalProperties:false — only the fields below are permitted; schema is NOT modified).
// The semantic.search.v0 contract requires an evidence_event on error; the human-readable
// degrade reason rides in `notes`.
fn evidence_event(action: &str, decision: &str, correlation_id: &str, notes: &str) -> serde_json::Value {
    let secs = now_secs();
    let seq = EVT_SEQ.fetch_add(1, Ordering::Relaxed);
    json!({
        "event_id": format!("evt-{}-{}", secs, seq),
        "ts": rfc3339_utc(secs),
        "action": action,
        "decision": decision,
        "correlation_id": correlation_id,
        "notes": notes
    })
}

fn main() {
    let mut sb = Schema::builder();
    let f_id = sb.add_text_field("id", STRING | STORED);
    let f_idx = sb.add_u64_field("idx", STORED | FAST);
    let f_title = sb.add_text_field("title", TEXT | STORED);
    let f_body = sb.add_text_field("body", TEXT | STORED);
    let schema = sb.build();
    let index = Index::create_in_ram(schema);
    let mut writer: tantivy::IndexWriter = index.writer(50_000_000).unwrap();

    let corpus_path =
        std::env::var("SHERLOCK_CORPUS").unwrap_or_else(|_| "corpus/frontier-labs.json".into());
    let data = std::fs::read_to_string(&corpus_path).expect("read corpus");
    let docs: Vec<Doc> = serde_json::from_str(&data).expect("parse corpus");
    for (i, d) in docs.iter().enumerate() {
        writer
            .add_document(doc!(
                f_id => d.id.clone(),
                f_idx => i as u64,
                f_title => d.title.clone(),
                f_body => d.body.clone()
            ))
            .unwrap();
    }
    writer.commit().unwrap();
    let reader = index.reader().unwrap();
    let qp = QueryParser::for_index(&index, vec![f_title, f_body]);

    // ── dense tier (optional): embed corpus → Qdrant (shared substrate) ─────────
    let agent = ureq::AgentBuilder::new()
        .timeout(Duration::from_secs(12))
        .build();
    let emb_url = std::env::var("EMBEDDINGS_URL").unwrap_or_default();
    let emb_model = std::env::var("EMBEDDINGS_MODEL").unwrap_or_else(|_| "nomic-embed-text".into());
    let qdrant_url = std::env::var("QDRANT_URL").unwrap_or_default().trim_end_matches('/').to_string();
    let coll = std::env::var("QDRANT_COLLECTION").unwrap_or_else(|_| "sherlock-corpus".into());
    let mut dense = false;
    if !emb_url.is_empty() && !qdrant_url.is_empty() {
        let mut vecs: Vec<(usize, Vec<f32>)> = Vec::new();
        let mut dim = 0usize;
        for (i, d) in docs.iter().enumerate() {
            if let Some(v) = embed(&agent, &emb_url, &emb_model, &format!("{}. {}", d.title, d.body)) {
                if dim == 0 {
                    dim = v.len();
                }
                if v.len() == dim {
                    vecs.push((i, v));
                }
            }
        }
        if !vecs.is_empty() {
            let _ = agent
                .put(&format!("{}/collections/{}", qdrant_url, coll))
                .send_json(json!({ "vectors": { "size": dim, "distance": "Cosine" } }));
            let points: Vec<serde_json::Value> = vecs
                .iter()
                .map(|(i, v)| json!({ "id": i, "vector": v, "payload": { "idx": i } }))
                .collect();
            if agent
                .put(&format!("{}/collections/{}/points?wait=true", qdrant_url, coll))
                .send_json(json!({ "points": points }))
                .is_ok()
            {
                dense = true;
                eprintln!("dense: embedded + upserted {} docs → qdrant '{}' (dim {})", vecs.len(), coll, dim);
            }
        }
        if !dense {
            eprintln!("dense disabled — embeddings/qdrant unreachable; BM25-only");
        }
    }

    let facet = |key: &dyn Fn(&Doc) -> String| -> BTreeMap<String, usize> {
        let mut m: BTreeMap<String, usize> = BTreeMap::new();
        for d in &docs {
            *m.entry(key(d)).or_insert(0) += 1;
        }
        m
    };

    let port = std::env::var("PORT").unwrap_or_else(|_| "8093".into());
    let server = tiny_http::Server::http(format!("127.0.0.1:{}", port)).unwrap();
    eprintln!("sherlock-engine on :{} — {} docs, mode={}", port, docs.len(), if dense { "hybrid (tantivy+qdrant/RRF)" } else { "tantivy BM25" });

    for request in server.incoming_requests() {
        let url = request.url().to_string();
        let path = url.split('?').next().unwrap_or("/");
        let body_str: String = if path == "/healthz" {
            json!({"ok": true, "service": "sherlock-engine", "engine": "tantivy", "dense": dense, "docs": docs.len()}).to_string()
        } else if path == "/facets" {
            json!({
                "doctype": serde_json::to_value(facet(&|d| d.doctype.clone())).unwrap(),
                "category": serde_json::to_value(facet(&|d| d.category.clone())).unwrap(),
                "region": serde_json::to_value(facet(&|d| d.region.clone())).unwrap()
            })
            .to_string()
        } else if path == "/search" {
            let raw = qparam(&url, "q").unwrap_or_default();
            let q = sanitize(&raw);
            let limit: usize = qparam(&url, "limit").and_then(|s| s.parse().ok()).unwrap_or(10);
            if q.trim().is_empty() {
                json!({"query": raw, "hits": [], "total": 0}).to_string()
            } else {
                let searcher = reader.searcher();
                // lexical
                let mut bm25_ranked: Vec<usize> = Vec::new();
                let mut bm25_score: HashMap<usize, f32> = HashMap::new();
                if let Ok(query) = qp.parse_query(q.trim()) {
                    if let Ok(top) = searcher.search(&query, &TopDocs::with_limit(limit * 2)) {
                        for (score, addr) in top {
                            if let Ok(d) = searcher.doc::<TantivyDocument>(addr) {
                                if let Some(OwnedValue::U64(n)) = d.get_first(f_idx) {
                                    let idx = *n as usize;
                                    bm25_ranked.push(idx);
                                    bm25_score.insert(idx, score);
                                }
                            }
                        }
                    }
                }
                // correlation id: echo caller's `cid` if provided, else mint one (contract:
                // "MUST include correlation_id ... echo"; required by evidence_event schema).
                let cid = qparam(&url, "cid")
                    .unwrap_or_else(|| format!("sherlock-{}-{}", now_secs(), EVT_SEQ.load(Ordering::Relaxed)));
                // dense — each failure is now RECORDED (degrade reason), not silently swallowed.
                let mut dense_ranked: Vec<usize> = Vec::new();
                let mut dense_score: HashMap<usize, f32> = HashMap::new();
                let mut degrade_reason: Option<&'static str> = None;
                if dense {
                    match embed(&agent, &emb_url, &emb_model, q.trim()) {
                        None => degrade_reason = Some("dense_unavailable: embed_failed"),
                        Some(qv) => match agent
                            .post(&format!("{}/collections/{}/points/search", qdrant_url, coll))
                            .send_json(json!({ "vector": qv, "limit": limit * 2, "with_payload": false }))
                        {
                            Err(_) => degrade_reason = Some("dense_unavailable: qdrant_error"),
                            Ok(resp) => match resp.into_json::<serde_json::Value>() {
                                Err(_) => degrade_reason = Some("dense_unavailable: qdrant_error"),
                                Ok(jv) => match jv.get("result").and_then(|r| r.as_array()) {
                                    None => degrade_reason = Some("dense_unavailable: empty_result"),
                                    Some(res) => {
                                        for item in res {
                                            if let Some(id) = item.get("id").and_then(|x| x.as_u64()) {
                                                let idx = id as usize;
                                                dense_ranked.push(idx);
                                                if let Some(s) = item.get("score").and_then(|x| x.as_f64()) {
                                                    dense_score.insert(idx, s as f32);
                                                }
                                            }
                                        }
                                        if dense_ranked.is_empty() {
                                            degrade_reason = Some("dense_unavailable: empty_result");
                                        }
                                    }
                                },
                            },
                        },
                    }
                }
                // Contract semantic.search.v0: MUST emit evidence_event on error. The dense
                // tier failing is an `error` decision for the dense backend; log it to the
                // audit sink (stderr) AND surface it in the response so it can't be hidden.
                let mut evidence: Vec<serde_json::Value> = Vec::new();
                if let Some(reason) = degrade_reason {
                    let ev = evidence_event("semantic.search.query", "error", &cid, reason);
                    eprintln!("evidence_event {}", ev);
                    evidence.push(ev);
                }
                // RRF fusion (k=60)
                let mut rrf: HashMap<usize, f64> = HashMap::new();
                for (rank, idx) in bm25_ranked.iter().enumerate() {
                    *rrf.entry(*idx).or_insert(0.0) += 1.0 / (60.0 + rank as f64 + 1.0);
                }
                for (rank, idx) in dense_ranked.iter().enumerate() {
                    *rrf.entry(*idx).or_insert(0.0) += 1.0 / (60.0 + rank as f64 + 1.0);
                }
                let mut fused: Vec<(usize, f64)> = rrf.into_iter().collect();
                fused.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
                fused.truncate(limit);
                let hits: Vec<serde_json::Value> = fused
                    .iter()
                    .map(|(idx, rrfscore)| {
                        let d = &docs[*idx];
                        json!({
                            "id": d.id, "title": d.title, "doctype": d.doctype, "category": d.category,
                            "region": d.region, "score": d.score,
                            "bm25": bm25_score.get(idx), "dense": dense_score.get(idx), "rrf": rrfscore,
                            "snippet": highlight(&d.body, q.trim())
                        })
                    })
                    .collect();
                // Honest provenance: label derives from THIS request's dense outcome, not the boot flag.
                let rm = retrieval_mode(dense, dense_ranked.len(), degrade_reason);
                let mut out = json!({
                    "query": raw,
                    "engine": rm.engine, // backward-compat; now "tantivy" on a real fallback, never a false hybrid claim
                    "retrieval_mode": { "lexical": rm.lexical, "dense": rm.dense, "fusion": rm.fusion },
                    "correlation_id": cid,
                    "total": hits.len(),
                    "hits": hits
                });
                if let Some(reason) = &rm.degraded {
                    out["degraded"] = json!(reason);
                }
                if !evidence.is_empty() {
                    out["evidence"] = json!(evidence);
                }
                out.to_string()
            }
        } else {
            json!({"error": "not found"}).to_string()
        };
        let mut resp = tiny_http::Response::from_string(body_str);
        resp.add_header(
            tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"application/json"[..]).unwrap(),
        );
        resp.add_header(
            tiny_http::Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap(),
        );
        let _ = request.respond(resp);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Reproduction of the OLD (buggy) label logic — keyed off the BOOT flag only.
    // Included so the red→green is explicit and can't silently rot: with dense
    // configured-on it ALWAYS returns the hybrid string, even for 0 dense hits.
    fn old_engine_label(dense_boot_flag: bool) -> &'static str {
        if dense_boot_flag { "tantivy+qdrant(rrf)" } else { "tantivy" }
    }

    #[test]
    fn red_old_logic_lies_when_dense_configured_but_empty() {
        // dense configured-on at boot, but request-time dense produced 0 hits.
        // The old code labels this "hybrid" — the false-provenance defect (D1).
        assert_eq!(old_engine_label(true), "tantivy+qdrant(rrf)");
    }

    // --- GREEN: request-time-derived label can no longer make that claim ---

    #[test]
    fn green_embed_failed_is_lexical_only_not_hybrid() {
        let rm = retrieval_mode(true, 0, Some("dense_unavailable: embed_failed"));
        assert_ne!(rm.engine, "tantivy+qdrant(rrf)", "must NOT claim hybrid when dense contributed nothing");
        assert_eq!(rm.engine, "tantivy");
        assert!(rm.lexical);
        assert!(!rm.dense);
        assert_eq!(rm.fusion, "none");
        assert_eq!(rm.degraded.as_deref(), Some("dense_unavailable: embed_failed"));
    }

    #[test]
    fn green_qdrant_error_is_lexical_only_not_hybrid() {
        let rm = retrieval_mode(true, 0, Some("dense_unavailable: qdrant_error"));
        assert_ne!(rm.engine, "tantivy+qdrant(rrf)");
        assert_eq!(rm.engine, "tantivy");
        assert_eq!(rm.fusion, "none");
        assert_eq!(rm.degraded.as_deref(), Some("dense_unavailable: qdrant_error"));
    }

    #[test]
    fn green_empty_result_is_lexical_only_not_hybrid() {
        let rm = retrieval_mode(true, 0, Some("dense_unavailable: empty_result"));
        assert_ne!(rm.engine, "tantivy+qdrant(rrf)");
        assert_eq!(rm.engine, "tantivy");
        assert_eq!(rm.degraded.as_deref(), Some("dense_unavailable: empty_result"));
    }

    #[test]
    fn green_genuine_hybrid_still_reports_hybrid() {
        // dense actually returned results this request → the hybrid claim is now EARNED.
        let rm = retrieval_mode(true, 3, None);
        assert_eq!(rm.engine, "tantivy+qdrant(rrf)");
        assert!(rm.dense);
        assert_eq!(rm.fusion, "rrf_k60");
        assert_eq!(rm.degraded, None);
    }

    #[test]
    fn green_dense_never_configured_is_lexical_without_degrade() {
        // dense not configured at all → lexical-only, but NOT "degraded" (nothing was promised).
        let rm = retrieval_mode(false, 0, None);
        assert_eq!(rm.engine, "tantivy");
        assert!(!rm.dense);
        assert_eq!(rm.fusion, "none");
        assert_eq!(rm.degraded, None);
    }

    #[test]
    fn evidence_event_conforms_to_contract_shape() {
        let ev = evidence_event("semantic.search.query", "error", "corr-x", "dense_unavailable: embed_failed");
        // Only schema-permitted keys, required ones present, decision in enum.
        assert_eq!(ev["decision"], "error");
        assert_eq!(ev["action"], "semantic.search.query");
        assert_eq!(ev["correlation_id"], "corr-x");
        assert_eq!(ev["notes"], "dense_unavailable: embed_failed");
        assert!(ev.get("event_id").and_then(|v| v.as_str()).is_some());
        let ts = ev["ts"].as_str().unwrap();
        assert!(ts.ends_with('Z') && ts.len() == 20, "ts not RFC3339: {ts}");
        // no field outside the frozen schema's allow-list
        let allowed = ["event_id", "ts", "action", "decision", "correlation_id", "notes"];
        for k in ev.as_object().unwrap().keys() {
            assert!(allowed.contains(&k.as_str()), "evidence_event emitted non-schema key: {k}");
        }
    }

    #[test]
    fn rfc3339_epoch_zero_is_1970() {
        assert_eq!(rfc3339_utc(0), "1970-01-01T00:00:00Z");
    }

    #[test]
    fn rfc3339_known_timestamp() {
        // 1_600_000_000 == 2020-09-13T12:26:40Z (independently verifiable)
        assert_eq!(rfc3339_utc(1_600_000_000), "2020-09-13T12:26:40Z");
    }
}
