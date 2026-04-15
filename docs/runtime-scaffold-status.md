# Sherlock-search runtime scaffold status

This branch now contains a minimal runnable service scaffold for the ProCybernetica dashboard payload.

## Added runtime files

- `package.json`
- `tsconfig.json`
- `.env.example`
- `src/server.ts`
- `src/procybernetica/buildDashboardPayload.ts`
- `src/routes/procybernetica-dashboard-route.ts`

## Intended runtime behavior

The service should expose:

- `GET /api/procybernetica/dashboard`

The route currently builds a payload from a configured data directory.

## Required environment

- `PORT`
- `PROCYBERNETICA_DATA_DIR`

## Remaining hardening work

- improve CSV parsing robustness
- add payload caching if needed
- add tests for payload shape and failure cases
- optionally replace direct file reads with a deeper scoring/export service
