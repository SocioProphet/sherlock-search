import assert from 'node:assert/strict';
import { buildScopeDGraphIndex, searchScopeDGraphIndex, ScopeDGraphExport } from '../src/scopeDGraphIndex';

const graph: ScopeDGraphExport = {
  schemaVersion: '0.1.0',
  graphExportId: 'cyber-graph-export:demo',
  generatedAt: '2026-06-28T00:00:00.000Z',
  sourceRefs: ['scope-d://demo'],
  executionPerformed: false,
  nodes: [
    {
      nodeId: 'indicator:sha256-demo',
      kind: 'indicator',
      label: 'sha256:aaaaaaaa',
      sourceRefs: ['scope-d://enrichment'],
      confidence: 0.8,
      provenanceHash: 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    },
    {
      nodeId: 'intelligence-receipt:virustotal-demo',
      kind: 'evidence_receipt',
      label: 'virustotal',
      sourceRefs: ['scope-d://enrichment'],
      confidence: 0.95,
      provenanceHash: 'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    },
    {
      nodeId: 'intelligence-observation:malware-demo',
      kind: 'observation',
      label: 'malware_reputation',
      sourceRefs: ['intelligence-receipt:virustotal-demo'],
      confidence: 0.86,
      provenanceHash: 'sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    },
    {
      nodeId: 'detection-candidate:arsenal-demo',
      kind: 'detection_candidate',
      label: 'SCOPE-D malware reputation via VirusTotal',
      sourceRefs: ['scope-d://detections'],
      confidence: 0.76,
      provenanceHash: 'sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
    },
    {
      nodeId: 'edge-bastion:cloudshell-fog',
      kind: 'edge_bastion',
      label: 'CloudShell Fog',
      sourceRefs: ['scope-d://detections'],
      confidence: 0.8,
      provenanceHash: 'sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
    },
  ],
  edges: [
    {
      edgeId: 'cyber-graph-runtime-edge:indicator-receipt',
      from: 'indicator:sha256-demo',
      predicate: 'produced_receipt',
      to: 'intelligence-receipt:virustotal-demo',
      sourceRefs: ['intelligence-receipt:virustotal-demo'],
      confidence: 0.9,
    },
    {
      edgeId: 'cyber-graph-runtime-edge:indicator-observation',
      from: 'indicator:sha256-demo',
      predicate: 'produced_observation',
      to: 'intelligence-observation:malware-demo',
      sourceRefs: ['intelligence-receipt:virustotal-demo'],
      confidence: 0.86,
    },
    {
      edgeId: 'cyber-graph-runtime-edge:observation-candidate',
      from: 'intelligence-observation:malware-demo',
      predicate: 'generated_candidate',
      to: 'detection-candidate:arsenal-demo',
      sourceRefs: ['intelligence-receipt:virustotal-demo'],
      confidence: 0.76,
    },
    {
      edgeId: 'cyber-graph-runtime-edge:candidate-cloudshell',
      from: 'detection-candidate:arsenal-demo',
      predicate: 'eligible_for_edge_bastion',
      to: 'edge-bastion:cloudshell-fog',
      sourceRefs: ['detection-candidate:arsenal-demo'],
      confidence: 0.8,
    },
  ],
};

const index = buildScopeDGraphIndex(graph, 'fixtures/cyber-graph-export.json');
assert.equal(index.schemaVersion, '0.1.0');
assert.equal(index.executionPerformed, false);
assert.equal(index.documents.length, graph.nodes.length + graph.edges.length);
assert.ok(index.documents.some((document) => document.documentType === 'evidence_receipt'));
assert.ok(index.documents.some((document) => document.documentType === 'detection_candidate'));
assert.ok(index.documents.some((document) => document.tags.includes('cloudshell-fog')));
assert.ok(index.documents.some((document) => document.tags.includes('arsenal')));

const malwareResults = searchScopeDGraphIndex(index, 'malware virustotal');
assert.ok(malwareResults.length >= 2);
assert.ok(malwareResults[0].confidence > 0);

const fogResults = searchScopeDGraphIndex(index, 'cloudshell fog');
assert.ok(fogResults.some((document) => document.title.includes('CloudShell Fog')));

assert.throws(() => buildScopeDGraphIndex({ ...graph, executionPerformed: true as false }), /refuses to index executing/);

console.log('SCOPE-D graph index tests passed.');
