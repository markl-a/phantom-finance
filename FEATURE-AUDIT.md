# phantom-finance — Feature Audit (2026-07-03)

Honest (NO-FAKING) audit of intended vs actually-implemented features. Verdicts
are judged by **reading the function bodies**, not docstrings, and cross-checked
against the test suite (127 tests, all passing).

## Intended scope (source files)

- `README.md` — quickstart + CLI surface + honest caveats
- `docs/phantom-finance.md` — the single canonical doc ("唯一主文件"): 已出貨 table
  (Tier 1→3) + visual roadmap (🚧/📅/🔭 = explicitly **not** shipped)
- `pyproject.toml` — `[project.scripts]`: `phantom-finance` (CLI) + `phantom-finance-mcp` (MCP server)
- `phantom_finance/cli.py` — the actual CLI subcommands (source of truth for shipped commands)
- `phantom_finance/mcp_server.py` — the registered MCP server; declares **exactly one** tool
- Supporting design docs: `docs/LEDGER_AND_SUMMARY_CONTRACT.md`,
  `docs/SUBSCRIPTION_AND_SCENARIO_CONTRACT.md`, `docs/PLANNING_SCENARIO_PROOF.md`

**Positioning (intended):** a small, local-first `ingest → categorize → report →
emit-event` pipeline with TW/zh-TW banking edge (Cathay/CTBC/E.SUN/Taishin + 民國
year), shame-free reports, and mesh event emission — deliberately NOT a full
budgeting app.

**Declared MCP tools:** `finance_monthly_summary(month, currency="TWD")` — the
ONLY tool exposed (`mcp_server.py:14-18`).

## Feature matrix

| Feature | Intended-from | Status | Evidence file:line | Notes |
|---|---|---|---|---|
| JSONL append-only ledger (Decimal e2e, sha256 txn_id dedupe, idempotent) | doc 已出貨, README | ✅ DONE | `ledger.py:25-157` | float rejected at boundary (`ledger.py:36-37`); test_ledger.py |
| Ledger crash-safety (exclusive lockfile + atomic tmp/replace + .bak) | doc Tier 1.5 | ✅ DONE | `ledger.py:104-156` | test_ledger_durability.py |
| `parse_amount` (NT$/$/元, thousands, accounting parens, trailing-minus) | README, doc | ✅ DONE | `ledger.py:59-89` | test_ledger.py |
| CSV ingest auto-detect (zh/en headers, BOM via utf-8-sig) | doc 已出貨, README | ✅ DONE | `ingest.py:48-73` | test_ingest.py |
| TW-bank presets (Cathay/CTBC/E.SUN/Taishin) + two-column credit/debit + skip_rows | doc Tier 2 | ✅ DONE | `presets.py:58-98`, `ingest.py:76-137` | Synthetic-fixture validated only; real-statement verify is **owner-gated** (honest note `presets.py:1-26`) |
| 民國 (ROC) year parsing | doc Tier 2 | ✅ DONE | `ingest.py:140-168` | ROC+1911; 4-digit always western; test_ingest/test_presets |
| Rule categorizer (80+ zh/en keywords, sign-based income fallback) | doc 已出貨 | ✅ DONE | `categorize.py:19-127` | test_categorize.py |
| User rules override + `recat MATCH CAT` learns durable rule + backfill | doc Tier 2 | ✅ DONE | `categorize.py:61-99`, `cli.py:167-186` | test_user_rules.py, test_correction_rule.py |
| LLM fallback hook (opt-in `PHANTOM_FINANCE_LLM`, offline-safe, mesh router) | doc Tier 2, README | ✅ DONE | `llm.py:22-66`, `categorize.py:111-127` | Hook + gating tested with a fake router; live `phantom_mesh.router` wiring is import-guarded and never exercised (offline-safe by design). test_llm.py |
| Monthly budgets (set/show, transfer excluded, over/ratio) | doc 已出貨 | ✅ DONE | `budget.py:29-77` | test_budget.py |
| Shame-free monthly markdown report | doc 已出貨 | ✅ DONE | `reporter.py:135-195,272-301` | "shame-free" asserted by test_reporter.py::test_render_is_shame_free |
| mesh event emission (events/ dir + meta.json) | doc 已出貨 | ✅ DONE | `events.py:15-30`, emitted `reporter.py:279-299` | test_reporter.py::test_write_report_creates_file_and_event |
| Multi-currency convert + net worth (rates.json, asset vs cash) | doc Tier 3 | ✅ DONE | `networth.py:37-52,135-160` | test_networth.py, test_networth_cli.py |
| Account mgmt (add/list/set-type → accounts.json) | doc Tier 3 | ✅ DONE | `networth.py:87-132`, `cli.py:147-165` | test_account_cli.py |
| Recurring / subscription detection (cadence via median gap) | doc Tier 2 | ✅ DONE | `recurring.py:52-101` | test_recurring.py |
| Price-hike detection + report section + event payload | doc Tier 2 follow-through | ✅ DONE | `recurring.py:104-109`, `reporter.py:164-170,289-297` | test_price_hike_report.py |
| Tax-prep summary (9A/9B/salary/other, NHI supplement, deductible candidates, withholding) | reporter/taxcat (impl) | ✅ DONE | `taxcat.py:46-77`, `reporter.py:109-132` | test_taxcat.py, test_tax_report.py |
| Quarterly report + quarter-level tax roll-up | reporter (impl), `report --quarter` | ✅ DONE | `reporter.py:198-269`, `cli.py:116-119` | test_tax_report.py::test_write_quarter_report_* |
| Aggregate monthly summary artifact (machine-readable JSON, no raw rows) | LEDGER_AND_SUMMARY_CONTRACT | ✅ DONE | `reporter.py:36-106`, `cli.py:122-131` | test_monthly_summary_contract.py |
| Subscription scenario demo bundle (synthetic-only what-if) | SUBSCRIPTION_AND_SCENARIO_CONTRACT | ✅ DONE | `scenario.py:117-172,383-402` | test_subscription_scenario_contract.py |
| Planning scenario bundle (runway, savings-goal, months-to-goal) | PLANNING_SCENARIO_PROOF | ✅ DONE | `scenario.py:212-312,405-424` | test_planning_scenario_contract.py |
| **MCP tool** `finance_monthly_summary` | pyproject `phantom-finance-mcp`, mcp_server | ✅ DONE | `mcp_server.py:14-18` | test_mcp_server.py |
| Recurring **persistence** + review state (recurring.json, new/reviewed/ignored) | doc 🚧 階段一 | ❌ MISSING | — | Detection only; no persistence/review. **Explicitly flagged NOT-shipped** in doc |
| Monthly report mobile/Telegram push | doc 🚧 階段一 | ❌ MISSING | — | Explicitly roadmap-future |
| `phantom skill` NL Q&A over ledger | doc 📅 階段二 | ❌ MISSING | — | Explicitly roadmap-future |
| Companion spend×behavior×health correlation | doc 🔭 階段三 | ❌ MISSING | — | Cross-project (companion side); explicitly roadmap-future |
| PTA Beancount/hledger export | doc 🔭 階段三+ | ❌ MISSING | — | Explicitly "only if needed" / roadmap-future |

## MCP server operability

**Verdict: WORKS (no startup hang).**

- `.venv/` exists and has `mcp` installed; `import mcp` and
  `import phantom_finance.mcp_server` both succeed (verified).
- Entrypoint `phantom-finance-mcp = phantom_finance.mcp_server:main` resolves;
  `main()` just calls `mcp.run()` (`mcp_server.py:21-23`).
- Top-level module code is trivial and non-blocking: it constructs
  `FastMCP("phantom-finance")` and registers one `@mcp.tool()` decorator
  (`mcp_server.py:11-18`). No network I/O, no blocking loop, no filesystem scan
  at import time — nothing that would stall `initialize` / `tools/list`.
- `initialize` / `tools/list` handlers are provided by FastMCP itself; the one
  tool `finance_monthly_summary` reads the local ledger lazily only when called.
- Only caveat: the MCP server requires the optional `mcp` extra
  (`pip install -e .[mcp]`). If a launcher starts it in a venv WITHOUT `mcp`, the
  top-level `from mcp.server.fastmcp import FastMCP` raises ImportError at start
  (fail-fast, not a hang). This project's `.venv` HAS it, so it starts cleanly.

## Test result

`.venv\Scripts\python -m pytest -q` → **127 passed in 2.12s** (0 failed, 0
skipped). Every shipped module has a corresponding test file (25 test files).

## Summary

**21 done / 0 untested / 0 partial / 5 missing of 26 total (≈81% real).**

The 5 "missing" items are **all explicitly flagged in the doc as NOT-yet-shipped**
roadmap work (🚧/📅/🔭), not silent gaps. Measured against what the doc *claims is
shipped* (the "已出貨" table + CLI surface + the 1 MCP tool), **21/21 = 100% are
genuinely implemented and tested** — this is an honest project with no faked
"done" claims and no stub/placeholder code found.

## Top gaps to close

1. **Recurring persistence + review state** (🚧 階段一): detection exists
   (`recurring.py`) but there is no `recurring.json` store and no
   new/reviewed/ignored review workflow — the cheapest, highest-value next step
   the doc itself prioritizes.
2. **Live LLM router integration is unexercised**: `llm.py` is offline-safe and
   the hook is tested with a fake router, but the real `phantom_mesh.router`
   import/complete path (`llm.py:34-39`) has no live/integration test — a latent
   integration risk when the mesh router is actually wired in.
3. **TW-bank presets lack real-statement validation** (owner-gated): presets are
   validated against synthetic fixtures only; a single redacted real Cathay/CTBC/
   E.SUN/Taishin export would confirm the header/date-format mappings.
