# Ledger And Summary Contract

This document defines the P2 public contract for the local ledger and monthly
summary artifact. It covers synthetic public demos and local user data, but it
does not turn this project into financial advice, tax advice, investment
advice, or a live bank-account aggregation service.

In short: this is not financial advice.

## Ledger JSONL

The ledger is append-only JSONL at `ledger.jsonl` under `PHANTOM_FINANCE_HOME`.
Each line is one transaction:

```json
{
  "date": "2026-06-01",
  "amount": "-150.50",
  "description": "Starbucks Xinyi",
  "account": "cathay",
  "category": "dining",
  "currency": "TWD",
  "txn_id": "stable-dedupe-id"
}
```

Rules:

- `amount` is a string decimal; negative is expense, positive is income.
- `date` is ISO `YYYY-MM-DD`.
- `txn_id` is used for idempotent imports.
- Ledger rows may contain private descriptions, so they are not public support
  artifacts.

## CSV Mapping

The synthetic public fixture `tests/fixtures/bank_en.csv` uses:

```csv
Date,Amount,Description
2026-06-01,"-150.50",Starbucks Xinyi
```

Auto-detection accepts English and Traditional Chinese bank-like headers for
date, amount, and description. Named TW-bank presets can also map bank-specific
headers. Public fixtures must stay synthetic.

## Local Config Files

- `rules.json`: JSON object of lowercase keyword to category, for example
  `{ "starbucks": "dining" }`.
- `budgets.json`: JSON object of category to monthly decimal string, for
  example `{ "dining": "600" }`.
- `accounts.json`: JSON object of account metadata, for example
  `{ "cathay": { "type": "cash", "currency": "TWD" } }`.
- `rates.json`: optional JSON object of currency to exchange-rate decimal
  string.

## Monthly Summary Artifact

Use `summary --month` for stable aggregate output:

```powershell
python -m phantom_finance.cli summary --month 2026-06 --json --out .\artifacts\summary-2026-06.json
```

Schema version 1:

```json
{
  "schema_version": 1,
  "month": "2026-06",
  "currency": "TWD",
  "transaction_count": 3,
  "income": "50000",
  "expense": "1350.50",
  "net": "48649.50",
  "net_worth": "48649.50",
  "spendable_cash": "48649.50",
  "by_category": [
    { "category": "groceries", "amount": "1200" },
    { "category": "dining", "amount": "150.50" }
  ],
  "budgets": [
    {
      "category": "dining",
      "spent": "150.50",
      "limit": "600",
      "ratio": 0.2508,
      "over": false
    }
  ]
}
```

The monthly summary is aggregate only. It intentionally omits transaction
descriptions and raw transaction rows, so it can be used as a safer automation
artifact while the private ledger remains local.

P2 schema version 1 assumes single-currency or already-normalized ledgers for
`income`, `expense`, `net`, and `by_category`. `net_worth` and
`spendable_cash` use the configured currency conversion path. Mixed-currency
category/income conversion is a later schema version, not a hidden claim in
this release slice.

## Public Demo Loop

The P2 synthetic loop is:

```powershell
python -m phantom_finance.cli account add cathay --type cash
python -m phantom_finance.cli import .\tests\fixtures\bank_en.csv --account cathay
python -m phantom_finance.cli recat Starbucks dining
python -m phantom_finance.cli budget set dining 600
python -m phantom_finance.cli summary --month 2026-06 --json --out .\artifacts\summary-2026-06.json
python -m phantom_finance.cli report --month 2026-06
python -m phantom_finance.cli net-worth
```

The loop uses synthetic data only and does not require bank credentials, network
access, broker access, or a cloud LLM.
