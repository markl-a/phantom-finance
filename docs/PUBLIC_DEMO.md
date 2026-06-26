# Public Demo Contract

`phantom-finance` public demos must use synthetic data only. The checked-in CSV
fixtures under `tests/fixtures/` are bank-like examples, not real account data.

This project is a local-first personal finance ledger and reporting tool. It is
not financial advice, tax advice, investment advice, or a bank-account
aggregation service.

## Isolated Smoke Demo

Run with isolated data roots so no real ledger is touched:

```powershell
$root = Join-Path $env:TEMP ("phantom-finance-demo-" + [guid]::NewGuid().ToString("N"))
$env:PHANTOM_MESH_HOME = Join-Path $root "mesh"
$env:PHANTOM_FINANCE_HOME = Join-Path $root "finance"

python -m phantom_finance.cli account add cathay --type cash
python -m phantom_finance.cli import .\tests\fixtures\bank_en.csv --account cathay
python -m phantom_finance.cli recat Starbucks dining
python -m phantom_finance.cli budget set dining 600
python -m phantom_finance.cli budget show --month 2026-06
python -m phantom_finance.cli summary --month 2026-06 --json --out (Join-Path $root "summary-2026-06.json")
python -m phantom_finance.cli scenario-demo --out (Join-Path $root "subscription-scenario")
python -m phantom_finance.cli planning-scenario --out (Join-Path $root "planning-scenario")
python -m phantom_finance.cli report --month 2026-06
python -m phantom_finance.cli net-worth

Remove-Item Env:\PHANTOM_MESH_HOME
Remove-Item Env:\PHANTOM_FINANCE_HOME
Remove-Item -LiteralPath $root -Recurse -Force
```

Expected shape:

- The import reads 3 synthetic transactions from `bank_en.csv`.
- The recategorization path can learn a local rule without calling an LLM.
- Budget status and monthly report are generated from the synthetic ledger.
- The monthly summary artifact is aggregate only and omits raw transaction rows.
- The synthetic subscription/scenario bundle writes aggregate-only
  `subscriptions.json` and `scenario.json` artifacts with
  `live_account_aggregation=false` and `financial_advice=false`.
- The P3 planning scenario proof writes aggregate-only `subscriptions.json` and
  `finance-scenario.json` artifacts with `synthetic_only=true`,
  `live_account_aggregation=false`, `bank_credentials_required=false`,
  `financial_advice=false`, `external_network=false`, and `cloud_llm=false`.
- The monthly report emits a local mesh event under the isolated
  `PHANTOM_MESH_HOME`; mesh event emission is local and optional.
- Net worth is computed from the same local ledger; no live account connection
  is used.

## Data Policy

- Do not commit real account numbers, card numbers, bank statements, tax records,
  private budgets, or personal reports.
- LLM-assisted categorization must remain optional and must not send private
  finance data by default.
- Public fixtures must stay synthetic and small enough to inspect in review.
