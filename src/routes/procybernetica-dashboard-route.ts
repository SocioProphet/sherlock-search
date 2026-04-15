import express from 'express';
import { buildDashboardPayload } from '../procybernetica/buildDashboardPayload';

const router = express.Router();

router.get('/api/procybernetica/dashboard', (_req, res) => {
  const dataDir = process.env.PROCYBERNETICA_DATA_DIR;

  if (!dataDir) {
    return res.status(503).json({
      generatedAtUtc: new Date().toISOString(),
      totals: {
        subjects: 0,
        labs: 0,
        models: 0,
        changedSubjects: 0,
        openEscalations: 0,
      },
      leaderboard: [],
      contradictions: [],
      status: 'unavailable',
      reason: 'PROCYBERNETICA_DATA_DIR is not configured.',
    });
  }

  try {
    const payload = buildDashboardPayload(dataDir);
    return res.json(payload);
  } catch (error) {
    const reason = error instanceof Error ? error.message : 'Unknown dashboard build failure';
    return res.status(500).json({
      generatedAtUtc: new Date().toISOString(),
      totals: {
        subjects: 0,
        labs: 0,
        models: 0,
        changedSubjects: 0,
        openEscalations: 0,
      },
      leaderboard: [],
      contradictions: [],
      status: 'error',
      reason,
    });
  }
});

export default router;
