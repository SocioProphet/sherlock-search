import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const readCsv = (filePath) => {
  const raw = fs.readFileSync(filePath, 'utf-8').trim();
  const [headerLine, ...rows] = raw.split(/\r?\n/);
  const header = headerLine.split(',');
  return rows.map((line) => {
    const values = line.split(',');
    return Object.fromEntries(header.map((key, index) => [key, values[index] ?? '']));
  });
};

const fixtureDir = path.resolve('fixtures');
const labs = readCsv(path.join(fixtureDir, 'procybernetica_full_lab_scoring.sample.csv'));
const models = readCsv(path.join(fixtureDir, 'procybernetica_model_family_scoring.sample.csv'));
const deltas = readCsv(path.join(fixtureDir, 'procybernetica_monitoring_deltas.sample.csv'));

const leaderboard = [...labs.map((row) => ({
  subjectType: 'Lab',
  subject: row['Lab'],
  composite: Number(row['Composite'] || 0),
})), ...models.map((row) => ({
  subjectType: 'Model',
  subject: row['Model family'],
  composite: Number(row['Composite'] || 0),
}))].sort((a, b) => b.composite - a.composite);

const changedSubjects = deltas.filter((row) => Number(row['total_change_count'] || 0) > 0).length;
const openEscalations = deltas.filter((row) => row['open_escalation_after_repeat'] === 'True').length;

assert.equal(labs.length, 3, 'expected three lab fixture rows');
assert.equal(models.length, 3, 'expected three model fixture rows');
assert.equal(changedSubjects, 2, 'expected two changed subjects');
assert.equal(openEscalations, 1, 'expected one open escalation');
assert.equal(leaderboard[0].subject, 'Claude Opus 4.6', 'expected model family to lead sample leaderboard');

console.log('Sherlock ProCybernetica dashboard smoke test passed.');
