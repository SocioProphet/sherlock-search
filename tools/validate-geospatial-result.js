#!/usr/bin/env node
'use strict';

const fs = require('fs');

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function loadJson(path) {
  try {
    return JSON.parse(fs.readFileSync(path, 'utf8'));
  } catch (error) {
    fail(`failed to read JSON ${path}: ${error.message}`);
  }
}

function requireField(obj, field, scope) {
  if (!Object.prototype.hasOwnProperty.call(obj, field)) {
    fail(`${scope} missing ${field}`);
  }
  return obj[field];
}

const path = process.argv[2];
if (!path) {
  console.error('Usage: node tools/validate-geospatial-result.js <record.json>');
  process.exit(2);
}

const record = loadJson(path);

const validSources = new Set(['GAIA', 'OFIF', 'LAMPSTAND', 'LATTICE_FORGE', 'PLATFORM', 'MEMORY', 'MIXED']);
const validEntityTypes = new Set([
  'DOCUMENT',
  'PROJECT',
  'MEMORY_NOTE',
  'WORLD_STATE_FEATURE',
  'EVIDENCE_ARTIFACT',
  'FIELD_EVENT',
  'OBSERVATION_EVENT',
  'DECISION_CARD',
  'MODEL_RUN',
  'MAP_LAYER',
  'RUNTIME_ASSET',
  'LOCAL_STATE_RECORD'
]);

requireField(record, 'record_version', 'record');
requireField(record, 'result_id', 'record');
const source = requireField(record, 'source', 'record');
const entityType = requireField(record, 'entity_type', 'record');
requireField(record, 'authority_ref', 'record');
requireField(record, 'title', 'record');
const provenanceRefs = requireField(record, 'provenance_refs', 'record');
const score = requireField(record, 'score', 'record');

if (record.record_version !== 'v1') fail('record_version must be v1');
if (!validSources.has(source)) fail(`invalid source ${source}`);
if (!validEntityTypes.has(entityType)) fail(`invalid entity_type ${entityType}`);
if (!Array.isArray(provenanceRefs) || provenanceRefs.length === 0) fail('provenance_refs must be non-empty array');
if (typeof score !== 'object' || score === null || typeof score.final !== 'number') fail('score.final must be numeric');

if (record.spatial_refs !== undefined && !Array.isArray(record.spatial_refs)) fail('spatial_refs must be array when present');
if (record.temporal_refs !== undefined && !Array.isArray(record.temporal_refs)) fail('temporal_refs must be array when present');
if (record.evidence_refs !== undefined && !Array.isArray(record.evidence_refs)) fail('evidence_refs must be array when present');
if (record.model_refs !== undefined && !Array.isArray(record.model_refs)) fail('model_refs must be array when present');
if (record.runtime_refs !== undefined && !Array.isArray(record.runtime_refs)) fail('runtime_refs must be array when present');

if ((source === 'GAIA' || source === 'OFIF') && (!Array.isArray(record.evidence_refs) || record.evidence_refs.length === 0)) {
  fail('GAIA/OFIF records must include evidence_refs');
}

console.log(`validated ${path}`);
