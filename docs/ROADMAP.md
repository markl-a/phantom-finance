# phantom-finance roadmap

## Tier 1 — shipped (2026-06-06)

- JSONL ledger: Decimal end-to-end, sha256 txn_id dedupe, idempotent re-import
- CSV ingest: zh/en header auto-detect, BOM, date normalization, `NT$1,234` parsing
- Rule categorizer (~70 zh/en keywords) + LLM fallback hook signature (defined but not yet wired into any code path)
- Monthly budgets (set/show, over-plan detection, transfers excluded)
- Shame-free monthly report → `~/.phantom-mesh/logs/phantom-finance/`
- Event emission → `~/.phantom-mesh/events/` (consumed by phantom-companion)

## Tier 2 — next

- Wire the LLM categorizer hook into the phantom-mesh model router
  (the `LlmCategorizer` callable signature in `categorize.py` is already stable)
- CSV presets for major TW banks (Cathay / CTBC / E.SUN / Taishin exports)
- Recurring-charge detection: subscription list + price-hike alerts
- phantom-companion side: spend × behavior × health correlation module

## Tier 3 — later

- Multi-currency with exchange rates (amounts already carry `currency`)
- Asset accounts (net worth, not just cash flow)
- `phantom skill` integration — "這個月外食多少?" answered via top-down skill
- Telegram / push delivery of the monthly report (shared with companion's Tier 2)

## Non-goals

- No cloud sync, no SaaS, no bank-API scraping with stored credentials —
  CSV export is the deliberate, sovereignty-preserving ingestion path.
- No investment advice. Reports state facts; decisions stay with the human.
