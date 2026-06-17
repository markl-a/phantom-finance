# phantom-finance roadmap

## Tier 1 — shipped (2026-06-06)

- JSONL ledger: Decimal end-to-end, sha256 txn_id dedupe, idempotent re-import
- CSV ingest: zh/en header auto-detect, BOM, date normalization, `NT$1,234` parsing
- Rule categorizer (80+ zh/en keywords) + stable LLM fallback hook signature
- Monthly budgets (set/show, over-plan detection, transfers excluded)
- Shame-free monthly report → `~/.phantom-mesh/logs/phantom-finance/`
- Event emission → `~/.phantom-mesh/events/` (consumed by phantom-companion)

## Tier 1.5 — durability (2026-06-17)

- Crash-safe ledger writes: exclusive lock-file + atomic temp/replace + `.bak`
  backup, so a crash mid-write can never tear a line or corrupt the ledger

## Tier 2 — shipped (2026-06-17)

- [x] Wire the LLM categorizer hook into the phantom-mesh model router
  (opt-in, offline-safe adapter in `llm.py`; `LlmCategorizer` signature unchanged)
- [x] CSV presets for major TW banks (Cathay / CTBC / E.SUN / Taishin exports),
  now actually threaded through the `--bank` CLI flag
- [x] User-defined `rules.json` overrides layered over the built-in categorizer
- [x] Recurring-charge detection: subscription list + price-hike alerts (`recurring.py`)
- phantom-companion side: spend × behavior × health correlation module — *deferred*

### Owner-gated (P2-2) — remaining by design, not capability

- Real-statement validation of the TW-bank presets is **owner-blocked**: the
  presets are validated against hand-authored synthetic fixtures only. No real
  or redacted bank export is available to verify field-by-field, so this stays
  open deliberately (see `presets.py` honesty note).

## Tier 3 — shipped (2026-06-17)

- [x] Multi-currency with exchange rates (`networth.py`: `rates.json` + `convert`)
- [x] Asset accounts: net worth vs spendable cash flow via `accounts.json`
- `phantom skill` integration — "這個月外食多少?" answered via top-down skill — *later*
- Telegram / push delivery of the monthly report — *later*

## Non-goals

- No cloud sync, no SaaS, no bank-API scraping with stored credentials —
  CSV export is the deliberate, sovereignty-preserving ingestion path.
- No investment advice. Reports state facts; decisions stay with the human.
