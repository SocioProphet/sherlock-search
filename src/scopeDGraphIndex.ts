export type ScopeDGraphNodeKind =
  | 'indicator'
  | 'provider'
  | 'observation'
  | 'evidence_receipt'
  | 'detection_candidate'
  | 'rule_family'
  | 'attack_technique'
  | 'deployment_target'
  | 'agent_workflow'
  | 'edge_bastion';

export interface ScopeDGraphNode {
  nodeId: string;
  kind: ScopeDGraphNodeKind;
  label: string;
  sourceRefs: string[];
  confidence: number;
  provenanceHash: string;
}

export interface ScopeDGraphEdge {
  edgeId: string;
  from: string;
  predicate: string;
  to: string;
  sourceRefs: string[];
  confidence: number;
}

export interface ScopeDGraphExport {
  schemaVersion: '0.1.0';
  graphExportId: string;
  generatedAt: string;
  sourceRefs: string[];
  nodes: ScopeDGraphNode[];
  edges: ScopeDGraphEdge[];
  executionPerformed: false;
}

export interface SherlockGraphDocument {
  documentId: string;
  documentType: ScopeDGraphNodeKind | 'graph_edge';
  title: string;
  body: string;
  tags: string[];
  sourceRefs: string[];
  confidence: number;
  rankSignals: {
    evidenceStrength: number;
    graphConnectivity: number;
    operationalPriority: number;
  };
}

export interface SherlockGraphIndex {
  schemaVersion: '0.1.0';
  indexId: string;
  sourceGraphRef: string;
  generatedAt: string;
  documents: SherlockGraphDocument[];
  executionPerformed: false;
}

const PRIORITY_BY_KIND: Record<string, number> = {
  detection_candidate: 0.95,
  evidence_receipt: 0.9,
  observation: 0.85,
  attack_technique: 0.8,
  indicator: 0.78,
  edge_bastion: 0.76,
  agent_workflow: 0.72,
  deployment_target: 0.7,
  provider: 0.65,
  rule_family: 0.62,
};

function edgeDegree(edges: ScopeDGraphEdge[], nodeId: string): number {
  return edges.filter((edge) => edge.from === nodeId || edge.to === nodeId).length;
}

function normalizeDegree(degree: number): number {
  return Math.min(1, degree / 8);
}

function tagsForNode(node: ScopeDGraphNode): string[] {
  const tags = ['scope-d', 'cyber-graph', node.kind];
  if (node.nodeId.startsWith('attack:')) tags.push('attack');
  if (node.nodeId.includes('cloudshell') || node.kind === 'edge_bastion') tags.push('cloudshell-fog');
  if (node.kind === 'detection_candidate') tags.push('arsenal');
  if (node.kind === 'evidence_receipt') tags.push('evidence');
  return Array.from(new Set(tags));
}

function tagsForEdge(edge: ScopeDGraphEdge): string[] {
  const tags = ['scope-d', 'cyber-graph', 'graph-edge', edge.predicate];
  if (edge.predicate.includes('attack')) tags.push('attack');
  if (edge.predicate.includes('grounded')) tags.push('evidence');
  if (edge.predicate.includes('edge_bastion') || edge.to.includes('cloudshell')) tags.push('cloudshell-fog');
  return Array.from(new Set(tags));
}

export function buildScopeDGraphIndex(graph: ScopeDGraphExport, sourceGraphRef = graph.graphExportId): SherlockGraphIndex {
  if (graph.executionPerformed !== false) {
    throw new Error('Sherlock refuses to index executing graph exports.');
  }
  if (!Array.isArray(graph.nodes) || graph.nodes.length === 0) {
    throw new Error('Scope-D graph export must include nodes.');
  }
  if (!Array.isArray(graph.edges) || graph.edges.length === 0) {
    throw new Error('Scope-D graph export must include edges.');
  }

  const nodeDocuments: SherlockGraphDocument[] = graph.nodes.map((node) => {
    const degree = edgeDegree(graph.edges, node.nodeId);
    const connectivity = normalizeDegree(degree);
    return {
      documentId: `sherlock-doc:${node.nodeId}`,
      documentType: node.kind,
      title: `${node.kind}: ${node.label}`,
      body: [
        `nodeId=${node.nodeId}`,
        `kind=${node.kind}`,
        `label=${node.label}`,
        `confidence=${node.confidence}`,
        `degree=${degree}`,
        `provenanceHash=${node.provenanceHash}`,
      ].join('\n'),
      tags: tagsForNode(node),
      sourceRefs: node.sourceRefs,
      confidence: node.confidence,
      rankSignals: {
        evidenceStrength: node.kind === 'evidence_receipt' ? 1 : node.confidence,
        graphConnectivity: connectivity,
        operationalPriority: PRIORITY_BY_KIND[node.kind] ?? 0.5,
      },
    };
  });

  const edgeDocuments: SherlockGraphDocument[] = graph.edges.map((edge) => ({
    documentId: `sherlock-doc:${edge.edgeId}`,
    documentType: 'graph_edge',
    title: `${edge.from} ${edge.predicate} ${edge.to}`,
    body: [
      `edgeId=${edge.edgeId}`,
      `from=${edge.from}`,
      `predicate=${edge.predicate}`,
      `to=${edge.to}`,
      `confidence=${edge.confidence}`,
    ].join('\n'),
    tags: tagsForEdge(edge),
    sourceRefs: edge.sourceRefs,
    confidence: edge.confidence,
    rankSignals: {
      evidenceStrength: edge.predicate === 'grounded_in' ? 1 : edge.confidence,
      graphConnectivity: 0.75,
      operationalPriority: edge.predicate === 'generated_candidate' ? 0.95 : 0.7,
    },
  }));

  return {
    schemaVersion: '0.1.0',
    indexId: `sherlock-scope-d-index:${graph.graphExportId.replace(/^cyber-graph-export:/, '')}`,
    sourceGraphRef,
    generatedAt: new Date().toISOString(),
    documents: [...nodeDocuments, ...edgeDocuments],
    executionPerformed: false,
  };
}

export function searchScopeDGraphIndex(index: SherlockGraphIndex, query: string): SherlockGraphDocument[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];
  const terms = normalized.split(/\s+/).filter(Boolean);
  return index.documents
    .map((document) => {
      const haystack = `${document.title}\n${document.body}\n${document.tags.join(' ')}`.toLowerCase();
      const lexicalScore = terms.reduce((score, term) => score + (haystack.includes(term) ? 1 : 0), 0) / terms.length;
      const rankScore = lexicalScore * 0.55
        + document.rankSignals.evidenceStrength * 0.2
        + document.rankSignals.graphConnectivity * 0.15
        + document.rankSignals.operationalPriority * 0.1;
      return { document, lexicalScore, rankScore };
    })
    .filter((result) => result.lexicalScore > 0)
    .sort((a, b) => b.rankScore - a.rankScore)
    .map((result) => result.document);
}
