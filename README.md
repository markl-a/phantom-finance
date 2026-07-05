# phantom-finance

[![CI](https://github.com/markl-a/phantom-finance/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-finance/actions/workflows/ci.yml)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

> **Local-first personal-finance engine for the phantom-mesh ecosystem.** Turns
> raw bank-CSV exports into private, shame-free monthly insight — ingest →
> categorize (rules + optional LLM) → budgets & reports → mesh events — with your
> transaction data never leaving the machine and no cloud bank-aggregation account.
>
> phantom-mesh 生活夥伴拼圖的**財務塊** — 銀行 CSV ingest → 規則(+ 可選 LLM)分類 → shame-free 月報 → mesh event,資料 local-first 永不離機。

## Quickstart

```powershell
python -m pip install -e .[test]
python -m pytest -q
python -m phantom_finance.cli --help
```

## MCP server

The MCP server ships in the **default** install — a plain `pip install -e .`
pulls in `mcp` and exposes the `phantom-finance-mcp` entry point, so the mesh can
wire it in without any extra:

```powershell
python -m pip install -e .
phantom-finance-mcp            # or: python -m phantom_finance.mcp_server
```

It serves one aggregate-only tool, `finance_monthly_summary(month, currency)`,
backed by the local ledger — no raw rows leave the machine.

Synthetic, isolated demo:

```powershell
$root = Join-Path $env:TEMP ("phantom-finance-demo-" + [guid]::NewGuid().ToString("N"))
$env:PHANTOM_MESH_HOME = Join-Path $root "mesh"
$env:PHANTOM_FINANCE_HOME = Join-Path $root "finance"

python -m phantom_finance.cli account add cathay --type cash
python -m phantom_finance.cli import .\tests\fixtures\bank_en.csv --account cathay
python -m phantom_finance.cli recat Starbucks dining
python -m phantom_finance.cli budget set dining 600
python -m phantom_finance.cli recurring list
python -m phantom_finance.cli summary --month 2026-06 --json --out (Join-Path $root "summary-2026-06.json")
python -m phantom_finance.cli scenario-demo --out (Join-Path $root "subscription-scenario")
python -m phantom_finance.cli planning-scenario --out (Join-Path $root "planning-scenario")
python -m phantom_finance.cli report --month 2026-06
python -m phantom_finance.cli net-worth

Remove-Item Env:\PHANTOM_MESH_HOME
Remove-Item Env:\PHANTOM_FINANCE_HOME
Remove-Item -LiteralPath $root -Recurse -Force
```

## Status

**Alpha, actively developed — the shipped surface is real, and covered by 148
passing tests** (every module has a matching test file). It runs both as a CLI
and as an **MCP server** (`phantom-finance-mcp`) that exposes the
`finance_monthly_summary` tool to the phantom mesh, so companion agents can pull
an aggregate-only monthly summary without touching raw rows.

Shipped and tested today:

- **Durable ledger** — append-only JSONL with Decimal-exact money, sha256
  transaction dedupe, and crash-safe writes (exclusive lockfile + atomic
  tmp/replace + `.bak`).
- **Bank-CSV ingest** — auto header detection (zh/en, BOM-safe) with Taiwan-bank
  presets (Cathay / CTBC / E.SUN / Taishin), two-column credit/debit, and 民國
  (ROC) year parsing.
- **Categorization** — rule engine over 80+ zh/en keywords with durable user
  overrides (`recat` learns a rule and backfills history) plus an opt-in,
  offline-safe LLM fallback routed through the mesh.
- **Recurring / subscription charges** — cadence detection with a **persistent
  review workflow** (`recurring.json`, `new → reviewed → ignored`) and price-hike
  alerts surfaced in the report.
- **Reports** — monthly budgets, shame-free markdown reports, quarterly roll-ups,
  and a tax-prep summary (9A/9B, NHI supplement, deductible candidates,
  withholding).
- **Net worth & summaries** — multi-currency conversion (asset vs cash) and a
  machine-readable monthly summary artifact (aggregate JSON, no raw rows).
- **Mesh integration** — emits a mesh event on each report so other phantom-mesh
  projects can react.

**Roadmap** (planned, not yet shipped): mobile / Telegram push of the monthly
report, natural-language Q&A over the ledger, spend × behavior × health
correlation with companion projects, and optional plain-text-accounting
(Beancount / hledger) export.

**Local-first & private:** all data lives on disk under `PHANTOM_FINANCE_HOME`
and never leaves the machine.

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
