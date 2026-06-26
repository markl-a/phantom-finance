# phantom-finance

[![CI](https://github.com/markl-a/phantom-finance/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-finance/actions/workflows/ci.yml)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

> phantom-mesh 生活夥伴拼圖的**財務塊** — 銀行 CSV ingest → 規則(+ 可選 LLM)分類 → shame-free 月報 → mesh event,資料 local-first 永不離機。

## Quickstart

```powershell
python -m pip install -e .[test]
python -m pytest -q
python -m phantom_finance.cli --help
```

Synthetic, isolated demo:

```powershell
$root = Join-Path $env:TEMP ("phantom-finance-demo-" + [guid]::NewGuid().ToString("N"))
$env:PHANTOM_MESH_HOME = Join-Path $root "mesh"
$env:PHANTOM_FINANCE_HOME = Join-Path $root "finance"

python -m phantom_finance.cli account add cathay --type cash
python -m phantom_finance.cli import .\tests\fixtures\bank_en.csv --account cathay
python -m phantom_finance.cli recat Starbucks dining
python -m phantom_finance.cli budget set dining 600
python -m phantom_finance.cli summary --month 2026-06 --json --out (Join-Path $root "summary-2026-06.json")
python -m phantom_finance.cli scenario-demo --out (Join-Path $root "subscription-scenario")
python -m phantom_finance.cli planning-scenario --out (Join-Path $root "planning-scenario")
python -m phantom_finance.cli report --month 2026-06
python -m phantom_finance.cli net-worth

Remove-Item Env:\PHANTOM_MESH_HOME
Remove-Item Env:\PHANTOM_FINANCE_HOME
Remove-Item -LiteralPath $root -Recurse -Force
```

This project is not financial advice, tax advice, investment advice, or a live
bank-account aggregation service. Public demos use synthetic fixtures only; see
[docs/PUBLIC_DEMO.md](docs/PUBLIC_DEMO.md). Ledger JSONL, local config, and
aggregate monthly summary schemas are documented in
[docs/LEDGER_AND_SUMMARY_CONTRACT.md](docs/LEDGER_AND_SUMMARY_CONTRACT.md).
The synthetic subscription and cashflow scenario bundle is documented in
[docs/SUBSCRIPTION_AND_SCENARIO_CONTRACT.md](docs/SUBSCRIPTION_AND_SCENARIO_CONTRACT.md).
The P3 recurring/net-worth planning scenario proof is documented in
[docs/PLANNING_SCENARIO_PROOF.md](docs/PLANNING_SCENARIO_PROOF.md).

📄 完整文件(定位 / 快速上手 / 狀態 + 路線圖 / 開源方向 / 刻意不做):見 [docs/phantom-finance.md](docs/phantom-finance.md)
