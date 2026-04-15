# Sherlock-search ProCybernetica runtime quickstart

## Purpose

This quickstart explains how to run the thin ProCybernetica dashboard payload service scaffold staged on this branch.

## Environment

Copy `.env.example` to `.env` and set:

- `PORT=8081`
- `PROCYBERNETICA_DATA_DIR=/absolute/path/to/procybernetica/data`

The configured data directory is expected to contain:
- `procybernetica_full_lab_scoring_v2_2026-04-12.csv`
- `procybernetica_model_family_scoring_seed_v1_2026-04-11.csv`
- `procybernetica_monitoring_deltas_v1_2026-04-12.csv`

## Start

```bash
yarn install
yarn dev
```

## Expected endpoint

When running, the service should expose:

- `GET /api/procybernetica/dashboard`

## Pairing with Socioprophet

Set on the Socioprophet server:

```bash
SHERLOCK_SEARCH_BASE_URL=http://localhost:8081
```

Then the Socioprophet proxy route can call through to the Sherlock payload service.
