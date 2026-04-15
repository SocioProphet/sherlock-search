# Socioprophet dashboard implementation notes

This note turns the payload contract branch into a code-facing implementation scaffold.

## Added code-facing files

- `src/procybernetica/buildDashboardPayload.ts`
- `src/routes/procybernetica-dashboard-route.ts`
- `schemas/procybernetica-dashboard-payload.schema.json`
- `examples/procybernetica-dashboard.payload.example.json`

## Current runtime assumption

The route scaffold reads from a data directory supplied by:

- `PROCYBERNETICA_DATA_DIR`

Expected files in that directory:
- `procybernetica_full_lab_scoring_v2_2026-04-12.csv`
- `procybernetica_model_family_scoring_seed_v1_2026-04-11.csv`
- `procybernetica_monitoring_deltas_v1_2026-04-12.csv`

## What remains to make this live

1. mount `src/routes/procybernetica-dashboard-route.ts` in the Sherlock-search server runtime
2. harden CSV parsing beyond the current minimal scaffold
3. optionally replace direct file reads with a scoring/export service call
4. expose cache headers or internal caching if payload build cost grows

## Architectural split reminder

- Sherlock-search owns payload build and search/discovery logic.
- Socioprophet owns the customer-facing React presentation and thin proxy route.
