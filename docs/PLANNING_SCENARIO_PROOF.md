# Planning Scenario Proof

This P3 scenario proves the public value of `phantom-finance` as a local-first
personal finance operating ledger. It connects recurring subscriptions,
monthly budgets, net worth, spendable cash, emergency runway, and a savings
goal into one deterministic local artifact bundle.

This is not financial advice. The bundle is arithmetic-only and uses synthetic
transactions generated in memory.

## Command

```powershell
python -m phantom_finance.cli planning-scenario --out .\artifacts\planning-scenario
```

The command writes:

- `manifest.json`
- `subscriptions.json`
- `finance-scenario.json`
- `summary.md`

It does not read bank credentials, does not connect to live accounts, does not
use network access, and does not call a cloud LLM.

## Manifest

Schema version 1:

```json
{
  "schema_version": 1,
  "mode": "synthetic_finance_planning_scenario",
  "synthetic_only": true,
  "live_account_aggregation": false,
  "bank_credentials_required": false,
  "financial_advice": false,
  "external_network": false,
  "cloud_llm": false,
  "artifacts": [
    "manifest.json",
    "subscriptions.json",
    "finance-scenario.json",
    "summary.md"
  ]
}
```

## Finance Scenario Artifact

`finance-scenario.json` records aggregate-only planning facts:

```json
{
  "schema_version": 1,
  "mode": "synthetic_finance_planning_scenario",
  "data_policy": "synthetic_only",
  "month": "2026-06",
  "currency": "TWD",
  "horizon_months": 6,
  "financial_advice": false,
  "live_account_aggregation": false,
  "bank_credentials_required": false,
  "raw_transaction_rows_included": false,
  "external_network": false,
  "cloud_llm": false,
  "summary": {
    "month": "2026-06",
    "monthly_income": "50000",
    "monthly_expense": "7970",
    "monthly_net": "42030",
    "net_worth": "186210",
    "spendable_cash": "186210",
    "subscription_count": 3,
    "subscription_latest_total": "1970"
  },
  "runway": {
    "monthly_expense": "7970",
    "runway_months": 23.36,
    "subscription_share_of_expense_pct": 24.72
  },
  "savings_goal": {
    "target_amount": "400000",
    "gap": "213790",
    "baseline_months_to_goal": 6,
    "pause_largest_subscription_months_to_goal": 5
  },
  "budgets": [
    {
      "category": "subscriptions",
      "spent": "1970",
      "limit": "2200",
      "remaining": "230",
      "ratio": 0.8955,
      "over": false
    }
  ],
  "scenarios": [
    {
      "name": "baseline_goal_path",
      "description": "Carry the current synthetic monthly net cashflow toward the savings goal.",
      "monthly_net": "42030",
      "projected_net_worth": "438390",
      "months_to_goal": 6
    },
    {
      "name": "pause_largest_subscription_goal_path",
      "description": "Arithmetic delta if the largest synthetic subscription were absent.",
      "affected_subscription": "City Gym",
      "monthly_net": "43230",
      "projected_net_worth": "445590",
      "months_to_goal": 5,
      "delta_vs_baseline": "7200"
    }
  ],
  "disclaimer": "Arithmetic planning scenario only; not financial advice."
}
```

The scenario rows compare the baseline synthetic cashflow against an arithmetic
what-if where the largest synthetic subscription is absent. The output is a
planning aid and must not be presented as a recommendation.

## Privacy Boundary

- Public planning scenario bundles are synthetic-only.
- Bundle artifacts must not include raw transaction rows.
- Bundle artifacts must not include real account numbers, card numbers, private
  statement lines, or bank credentials.
- Live account aggregation is out of scope.
- Cloud LLM use is out of scope.
- Merchant labels in `subscriptions.json` are synthetic fixture labels, not
  private statement descriptions.

## Compatibility

- `schema_version` is the compatibility key for parsers.
- New optional top-level fields may be added later.
- Existing fields in schema version 1 must keep their meaning until a new
  schema version is introduced.
