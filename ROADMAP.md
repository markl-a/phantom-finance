# phantom-finance roadmap

> ⭐ This file is the **single source of truth for project status.** README and other
> docs link here instead of carrying their own status lists. Every "Shipped" bullet is
> grounded in a real commit on `master` (merge or feature commit, hash cited inline).
> Last reconciled **2026-06-19**.

## Shipped

### Tier 1 — core ledger + report (2026-06-06)

- JSONL ledger: Decimal end-to-end, sha256 `txn_id` dedupe, idempotent re-import
- CSV ingest: zh/en header auto-detect, BOM, date normalization, `NT$1,234` parsing
- Rule categorizer (80+ zh/en keywords) + stable LLM fallback hook signature
- Monthly budgets (set/show, over-plan detection, transfers excluded)
- Shame-free monthly report → `~/.phantom-mesh/logs/phantom-finance/`
- Event emission → `~/.phantom-mesh/events/` (consumed by phantom-companion)
- _(commit `891b461` Tier 1 baseline)_

### Tier 1.5 — durability (2026-06-17)

- Crash-safe ledger writes: exclusive lock-file + atomic temp/replace + `.bak`
  backup, so a crash mid-write can never tear a line or corrupt the ledger
- _(commit `498cab3`)_

### Tier 2 — LLM hook, TW-bank presets, user rules, recurring (2026-06-17)

- LLM categorizer hook wired into the phantom-mesh model router (opt-in,
  offline-safe adapter in `llm.py`; `LlmCategorizer` signature unchanged) —
  _(commit `2602ec0`)_
- CSV presets for major TW banks (Cathay / CTBC / E.SUN / Taishin exports),
  threaded through the `--bank` CLI flag (auto-detect preserved when absent) —
  _(commits `ea0ed3b`, `09ee90d`)_
- ROC (民國) year parsing in date normalization — _(commit `3d8451d`)_
- User-defined `rules.json` overrides layered over the built-in categorizer —
  _(commit `09ee90d`)_
- Recurring-charge detection: subscription list + price-hike alerts
  (`recurring.py`) — _(commit `7f8284d`)_
- _(reconciled to final form in merge `d8801ee`)_

### Tier 3 — multi-currency + net worth (2026-06-17 → 2026-06-18)

- Multi-currency with exchange rates (`networth.py`: `rates.json` + `convert`) —
  _(commit `daefed6`)_
- Asset accounts: net worth vs spendable cash flow via `accounts.json` —
  _(commit `daefed6`)_
- `account add` / `account list` / `account set-type` CLI writes `accounts.json`
  so net worth is usable without hand-editing JSON; e2e proves net worth includes
  asset accounts and cash flow excludes them — _(merge `5f969b7`)_
- `net-worth [--currency]` CLI command surfaces the existing
  `net_worth()` / `cashflow_total()` (no duplicated math) + a net-worth /
  spendable-cash line in the monthly report — _(merge `eae292b`)_

### Tier 2 follow-through — price-hike alerts reach the user (2026-06-18)

- The monthly report renders a "Subscription price changes" section via the
  existing `recurring.price_hikes()` (shame-free wording), and the emitted
  monthly-report event payload now carries the detected price hikes — closing the
  gap where `price_hikes()` was dead code referenced only by tests — _(merge `7cea460`)_

## In progress

- _Nothing currently in flight on `master`._ Open dev branches exist for
  recurring-charge persistence and related surfaces; see "Planned-next" for what
  they cover and the remote-branch list in the consolidation report.

## Planned-next

- **Recurring-charge persistence + review state**: persist detected recurring
  charges to `recurring.json` with a per-item review status (new / reviewed /
  ignored) and `recurring review` / `recurring list` subcommands, so detection
  becomes a stateful, reviewable feature rather than print-only.
- **phantom-companion correlation**: spend × behavior × health correlation module
  on the companion side (deferred — depends on companion keystone work).
- **`phantom skill` integration**: answer top-down questions like
  「這個月外食多少?」 through a skill rather than a bespoke command.
- **Push delivery of the monthly report**: Telegram / phone push of the report
  (today the mesh event is the delivery; an actual phone push is future).

### Owner-gated (not a capability gap)

- **Real-statement validation of the TW-bank presets** is owner-blocked: the
  presets are validated against hand-authored synthetic fixtures only. No real or
  redacted bank export is available to verify field-by-field, so this stays open
  deliberately (see the honesty note in `presets.py`).

## Non-goals

- No cloud sync, no SaaS, no bank-API scraping with stored credentials — CSV
  export is the deliberate, sovereignty-preserving ingestion path.
- No investment advice. Reports state facts; decisions stay with the human.
