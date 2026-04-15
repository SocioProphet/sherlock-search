# Socioprophet dashboard contract

This note defines the intended handshake between `SocioProphet/sherlock-search` and the customer-facing dashboard scaffold staged in `SocioProphet/socioprophet`.

## Goal

Provide one stable HTTP payload that the Socioprophet web server can proxy and the React client can render.

## Intended endpoint

- `GET /api/procybernetica/dashboard`

## Response shape

```json
{
  "generatedAtUtc": "2026-04-14T00:00:00Z",
  "totals": {
    "subjects": 120,
    "labs": 100,
    "models": 20,
    "changedSubjects": 7,
    "openEscalations": 3
  },
  "leaderboard": [],
  "contradictions": []
}
```

## Minimum semantics

- `generatedAtUtc` must reflect the payload build time.
- `totals` must summarize the delivered body.
- `leaderboard` should contain ranked lab/model entries for display.
- `contradictions` should contain the subset flagged for constitutional risk or contradiction review.

## Integration rule

The payload should be treated as a view/export surface. Sherlock-search remains the search/discovery and evidence side; Socioprophet remains the customer-facing presentation side.
