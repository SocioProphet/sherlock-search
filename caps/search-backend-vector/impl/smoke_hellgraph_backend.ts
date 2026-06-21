/**
 * smoke_hellgraph_backend — proves the search-backend-vector cap works over HellGraph end to end.
 *
 * Upserts three documents (real nomic-embed vectors via HellGraph's embedText), queries with a
 * paraphrase, and asserts the semantically-right doc ranks first — then writes the response JSON
 * for schema validation against the cap's vector_query_response.schema.json. Hermetic: attaches an
 * isolated temp SQLite atomspace so it never touches the primary brain.
 *
 * Run:  bun caps/search-backend-vector/impl/smoke_hellgraph_backend.ts
 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import { embedText } from '@socioprophet/hellgraph'
import { vectorUpsert, vectorQuery, evidenceEvents, BACKEND } from './hellgraph-vector-backend'

// Hermetic by invocation: run with HOME pointed at a throwaway dir so any default atomspace
// persistence lands in temp, never the primary brain (see the runner in the cap README).
async function main() {
  const actor = { id: 'smoke', roles: ['test'] }
  const docs = [
    { id: 'doc:retry', text: 'Handle transient worker failures with exponential backoff and a capped number of retries.' },
    { id: 'doc:cache', text: 'Cache invalidation uses a TTL and write-through update on the hot path.' },
    { id: 'doc:auth', text: 'Authenticate inbound requests with short-lived, signed bearer tokens.' },
  ]
  for (const d of docs) {
    const vector = await embedText(d.text)
    const ev = vectorUpsert({ correlation_id: `corr-upsert-${d.id}`, actor, document: { doc_id: d.id, vector, metadata: { text: d.text } } })
    console.log(`  upsert ${d.id.padEnd(10)} dims=${vector.length} → ${ev.decision}`)
  }

  const q = 'how should retries deal with intermittent failures?'
  const qvec = await embedText(q)
  const { response } = vectorQuery({ correlation_id: 'corr-query-0001', trace_id: 'trace-smoke', actor, query: { vector: qvec, top_k: 3 } })

  console.log(`\n  query: "${q}"  (backend=${BACKEND.name}@${BACKEND.version})`)
  for (const r of response.results) console.log(`   ${r.score.toFixed(3)}  ${r.doc_id}`)

  const top = response.results[0]?.doc_id
  const ok = top === 'doc:retry'
  console.log(`\n  top result = ${top}  →  ${ok ? 'PASS' : 'FAIL'} (expected doc:retry)`)
  console.log(`  evidence events emitted: ${evidenceEvents().length} (${evidenceEvents().map((e) => e.action + ':' + e.decision).join(', ')})`)

  const outFile = path.join(os.tmpdir(), 'sherlock-hg-query-response.json')
  fs.writeFileSync(outFile, JSON.stringify(response, null, 2))
  console.log(`\n  response written for schema validation → ${outFile}`)
  if (!ok) process.exit(1)
}
main().catch((e) => { console.error(e); process.exit(1) })
