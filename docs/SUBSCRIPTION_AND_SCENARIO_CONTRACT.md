# Subscription And Scenario Contract

This document defines the P2 public contract for the synthetic subscription and
cashflow scenario demo. It does not turn `phantom-finance` into financial
advice, tax advice, investment advice, or a live account aggregation service.

In short: this is not financial advice.

## Command

```powershell
python -m phantom_finance.cli scenario-demo --out .\artifacts\subscription-scenario
```

The command writes a deterministic synthetic bundle:

- `manifest.json`
- `subscriptions.json`
- `scenario.json`
- `summary.md`

The bundle is generated from in-memory synthetic transactions. It does not read
bank credentials, does not connect to live accounts, does not use network
access, and does not call a cloud LLM.

## Manifest

Schema version 1:

```json
{
  "schema_version": 1,
  "mode": "synthetic_subscription_scenario_loop",
  "synthetic_only": true,
  "live_account_aggregation": false,
  "bank_credentials_required": false,
  "financial_advice": false,
  "external_network": false,
  "cloud_llm": false,
  "artifacts": [
    "manifest.json",
    "subscriptions.json",
    "scenario.json",
    "summary.md"
  ]
}
```

## Subscriptions Artifact

`subscriptions.json` records recurring/subscription-like aggregate rows:

```json
{
  "schema_version": 1,
  "mode": "synthetic_subscription_detection",
  "data_policy": "synthetic_only",
  "raw_transaction_rows_included": false,
  "subscriptions": [
    {
      "label": "City Gym",
      "cadence": "monthly",
      "occurrences": 4,
      "typical_amount": "1200",
      "latest_amount": "1200",
      "first_date": "2026-03-10",
      "last_date": "2026-06-10",
      "price_increased": false,
      "pct_change": 0.0
    }
  ]
}
```

It intentionally omits raw transaction rows, account numbers, card numbers,
bank statement lines, and original private descriptions.

## Scenario Artifact

`scenario.json` is an arithmetic what-if artifact:

```json
{
  "schema_version": 1,
  "mode": "synthetic_subscription_scenario_loop",
  "data_policy": "synthetic_only",
  "month": "2026-06",
  "currency": "TWD",
  "horizon_months": 3,
  "financial_advice": false,
  "live_account_aggregation": false,
  "bank_credentials_required": false,
  "raw_transaction_rows_included": false,
  "disclaimer": "Arithmetic what-if only; not financial advice.",
  "summary": {
    "month": "2026-06",
    "income": "50000",
    "expense": "7970",
    "net": "42030",
    "subscription_count": 3,
    "subscription_latest_total": "1970"
  },
  "scenarios": [
    {
      "name": "baseline",
      "description": "Carry the current synthetic monthly net cashflow forward.",
      "monthly_net": "42030",
      "projected_delta": "126090"
    }
  ]
}
```

Scenario rows are arithmetic projections only. They are not recommendations and
must not be presented as advice.

## Privacy Boundary

- Public scenario bundles must be synthetic-only.
- Bundle artifacts must not include raw transaction rows.
- Bundle artifacts must not include real account numbers, card numbers, private
  statement lines, or bank credentials.
- Live account aggregation is out of scope for this release slice.
- Cloud LLM use is out of scope for this release slice.
