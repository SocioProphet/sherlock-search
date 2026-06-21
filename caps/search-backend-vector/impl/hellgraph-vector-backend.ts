/**
 * hellgraph-vector-backend — the search-backend-vector capability, implemented over HellGraph.
 *
 * Sherlock owns Anchor -> Normalize -> Propose and needs a vector retrieval backend behind its
 * `vectorCandidates`. This binds that backend to HellGraph's atomspace: documents are upserted as
 * DocumentChunk atoms carrying their embedding, and a query vector is scored by cosine over those
 * atoms. So Sherlock's vector lane and the Noetica/SourceOS brain are ONE store — a vector
 * candidate Sherlock proposes is anchored in the same graph the agent reasons over, and (per the
 * evidence-answer contract) stays `candidate_only` until Holmes verifies and Policy admits.
 *
 * Honours the cap contracts exactly:
 *   in:  schemas/vector_upsert.schema.json      (correlation_id, actor, document{doc_id, vector, metadata?})
 *        schemas/vector_query.schema.json        (correlation_id, actor, query{vector, top_k?})
 *   out: schemas/vector_query_response.schema.json (correlation_id, results[{doc_id, score, distance}], backend)
 *        schemas/evidence_event.schema.json       (every op emits an allow/deny/error audit event)
 *
 * Pure functions over an injected HellGraph singleton; the Sherlock service wires the routes and
 * ships the evidence events to its governed evidence lane.
 */
import { createHash, randomUUID } from 'node:crypto'
import { getHellGraph, putChunk, cosineSim } from '@socioprophet/hellgraph'

export const BACKEND = { name: 'hellgraph-vector', kind: 'vector' as const, version: '0.1.0' }
const CHUNK_LABEL = 'DocumentChunk'

export interface Actor { id: string; roles?: string[] }
export interface VectorUpsertRequest { correlation_id: string; trace_id?: string; actor: Actor; document: { doc_id: string; vector: number[]; metadata?: Record<string, unknown> } }
export interface VectorQueryRequest { correlation_id: string; trace_id?: string; actor: Actor; query: { vector: number[]; top_k?: number } }
export interface VectorResult { doc_id: string; score: number; distance: number }
export interface VectorQueryResponse { correlation_id: string; trace_id?: string; results: VectorResult[]; backend: typeof BACKEND }
export interface EvidenceEvent {
  event_id: string; ts: string; actor?: object; action: string
  decision: 'allow' | 'deny' | 'error'; correlation_id: string; trace_id?: string
  input_hash?: string | null; output_hash?: string | null; policy_id?: string | null; rule_id?: string | null
}

// In-process audit sink — the Sherlock service drains this onto its governed evidence lane.
const sink: EvidenceEvent[] = []
export function evidenceEvents(): readonly EvidenceEvent[] { return sink }
export function clearEvidence(): void { sink.length = 0 }

const sha = (o: unknown): string => 'sha256:' + createHash('sha256').update(JSON.stringify(o)).digest('hex').slice(0, 32)

function emit(action: string, decision: EvidenceEvent['decision'], req: { correlation_id: string; trace_id?: string; actor?: Actor }, input: unknown, output: unknown): EvidenceEvent {
  const e: EvidenceEvent = {
    event_id: randomUUID(), ts: new Date().toISOString(), actor: req.actor, action, decision,
    correlation_id: req.correlation_id, trace_id: req.trace_id,
    input_hash: input == null ? null : sha(input), output_hash: output == null ? null : sha(output),
    policy_id: null, rule_id: null,
  }
  sink.push(e)
  return e
}

/** Only scalar metadata survives onto the chunk atom (putChunk meta is string|number). */
function scalarMeta(m?: Record<string, unknown>): Record<string, string | number> {
  const o: Record<string, string | number> = {}
  for (const [k, v] of Object.entries(m ?? {})) if (typeof v === 'string' || typeof v === 'number') o[k] = v
  return o
}

/** Upsert one document's vector into HellGraph as a DocumentChunk atom (idempotent per doc_id). */
export function vectorUpsert(req: VectorUpsertRequest): EvidenceEvent {
  const d = req.document
  if (!d?.doc_id || !Array.isArray(d.vector) || d.vector.length === 0) {
    return emit('vector.upsert', 'error', req, d, null)
  }
  putChunk({
    docId: d.doc_id, idx: 0, vec: d.vector,
    text: String(d.metadata?.['text'] ?? ''),
    filename: String(d.metadata?.['filename'] ?? d.doc_id),
    meta: { backend: BACKEND.name, ...scalarMeta(d.metadata) },
  })
  return emit('vector.upsert', 'allow', req, { doc_id: d.doc_id, dims: d.vector.length }, { doc_id: d.doc_id })
}

/** Score a query vector by cosine over every embedded DocumentChunk; return the top_k as the
 *  cap response, and the audit event. distance = 1 - cosine. */
export function vectorQuery(req: VectorQueryRequest): { response: VectorQueryResponse; event: EvidenceEvent } {
  const k = req.query?.top_k ?? 20
  const qv = req.query?.vector ?? []
  const g = getHellGraph()
  const results: VectorResult[] = []
  if (qv.length) {
    for (const n of g.nodesByLabel(CHUNK_LABEL)) {
      const raw = String(n.properties['embedding'] ?? '')
      if (!raw) continue
      let v: number[]
      try { v = JSON.parse(raw) as number[] } catch { continue }
      const score = cosineSim(qv, v)
      results.push({ doc_id: String(n.properties['doc_id'] ?? ''), score, distance: 1 - score })
    }
    results.sort((a, b) => b.score - a.score)
  }
  const top = results.slice(0, k)
  const response: VectorQueryResponse = { correlation_id: req.correlation_id, trace_id: req.trace_id, results: top, backend: BACKEND }
  const event = emit('vector.query', qv.length ? 'allow' : 'error', req, { top_k: k, dims: qv.length }, { n: top.length })
  return { response, event }
}
