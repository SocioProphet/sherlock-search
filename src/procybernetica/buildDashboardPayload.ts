import fs from 'node:fs';
import path from 'node:path';

export type DashboardRow = {
  subjectType: 'Lab' | 'Model';
  subject: string;
  regionOrOwner: string;
  category: string;
  poa: number;
  ega: number;
  composite: number;
  evidenceConfidence: string;
  topStrength: string;
  topRisk: string;
  scoringBasis: string;
};

export type DashboardPayload = {
  generatedAtUtc: string;
  totals: {
    subjects: number;
    labs: number;
    models: number;
    changedSubjects: number;
    openEscalations: number;
  };
  leaderboard: DashboardRow[];
  contradictions: DashboardRow[];
};

const parseCsv = (input: string): string[][] =>
  input
    .trim()
    .split(/\r?\n/)
    .map((line) => line.split(','));

const toRows = (csvPath: string): Record<string, string>[] => {
  const raw = fs.readFileSync(csvPath, 'utf-8');
  const rows = parseCsv(raw);
  const [header, ...body] = rows;
  return body.map((row) => Object.fromEntries(header.map((key, index) => [key, row[index] ?? ''])));
};

export const buildDashboardPayload = (dataDir: string): DashboardPayload => {
  const scoringPath = path.join(dataDir, 'procybernetica_full_lab_scoring_v2_2026-04-12.csv');
  const modelPath = path.join(dataDir, 'procybernetica_model_family_scoring_seed_v1_2026-04-11.csv');
  const deltasPath = path.join(dataDir, 'procybernetica_monitoring_deltas_v1_2026-04-12.csv');

  const labs = toRows(scoringPath).map((row) => ({
    subjectType: 'Lab' as const,
    subject: row['Lab'],
    regionOrOwner: row['Region bucket'],
    category: row['Dossier class'],
    poa: Number(row['POA'] || 0),
    ega: Number(row['EGA'] || 0),
    composite: Number(row['Composite'] || 0),
    evidenceConfidence: row['Evidence confidence'] || 'Unknown',
    topStrength: 'Operational visibility',
    topRisk: 'Needs deeper evidence',
    scoringBasis: row['Scoring basis'] || 'Heuristic seed',
  }));

  const models = toRows(modelPath).map((row) => ({
    subjectType: 'Model' as const,
    subject: row['Model family'],
    regionOrOwner: 'Model family',
    category: 'Frontier model family',
    poa: Number(row['POA'] || 0),
    ega: Number(row['EGA'] || 0),
    composite: Number(row['Composite'] || 0),
    evidenceConfidence: row['Evidence confidence'] || 'Unknown',
    topStrength: 'Operational fit',
    topRisk: 'Needs deeper evidence',
    scoringBasis: 'Seed calibration',
  }));

  const deltas = toRows(deltasPath);
  const changedSubjects = deltas.filter((row) => Number(row['total_change_count'] || 0) > 0).length;
  const openEscalations = deltas.filter((row) => row['open_escalation_after_repeat'] === 'True').length;

  const leaderboard = [...labs, ...models]
    .sort((a, b) => b.composite - a.composite)
    .slice(0, 25);

  const contradictions = labs.filter((row) => row.topRisk.toLowerCase().includes('evidence')).slice(0, 12);

  return {
    generatedAtUtc: new Date().toISOString(),
    totals: {
      subjects: labs.length + models.length,
      labs: labs.length,
      models: models.length,
      changedSubjects,
      openEscalations,
    },
    leaderboard,
    contradictions,
  };
};
