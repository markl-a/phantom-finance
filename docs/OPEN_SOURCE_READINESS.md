# Open Source Readiness

Project: `phantom-finance`
Current phase: P3 recurring/net-worth planning scenario proof slice verified
Master plan: `../../PHANTOM-SATELLITES-OPEN-SOURCE-MASTER-PLAN.md`

## Shipped Features

- Local-first personal finance CLI.
- CLI entrypoint: `phantom-finance = phantom_finance.cli:main`.
- Help surface verified with `python -m phantom_finance.cli --help`.
- Subcommands include `add`, `import`, `summary`, `report`, `budget`, `account`, `recat`, `recurring`, and `net-worth`.
- Root README points to `docs/phantom-finance.md`.
- Root README now includes an isolated synthetic quickstart and a finance disclaimer.
- Public demo/data policy is documented in `docs/PUBLIC_DEMO.md`.
- Ledger JSONL, CSV mapping, local config, and aggregate summary schemas are documented in `docs/LEDGER_AND_SUMMARY_CONTRACT.md`.
- CLI supports `summary --month --json --out` for aggregate-only monthly JSON artifacts.
- Synthetic subscription and cashflow scenario schemas are documented in `docs/SUBSCRIPTION_AND_SCENARIO_CONTRACT.md`.
- CLI supports `scenario-demo --out` for deterministic synthetic subscription/scenario artifact bundles.
- Scenario bundles include `manifest.json`, `subscriptions.json`, `scenario.json`, and `summary.md`; they are synthetic-only, aggregate-only, not financial advice, and do not require live account aggregation.
- P3 recurring/net-worth planning scenario proof is documented in `docs/PLANNING_SCENARIO_PROOF.md`.
- CLI supports `planning-scenario --out` for deterministic synthetic planning scenario artifact bundles.
- Planning scenario bundles include `manifest.json`, `subscriptions.json`, `finance-scenario.json`, and `summary.md`; they connect subscriptions, budgets, net worth, spendable cash, runway, and a savings goal without live aggregation or advice claims.
- Test suite baseline after planning scenario additions: `python -m pytest -q` passed with 118 tests.

## Planned Or Deferred Features

- Broader finance operating ledger: richer account model, savings goals, household mode, and optional mesh events.
- P3 follow-up work remains for broader account model and goal ergonomics beyond the synthetic planning scenario proof.
- Live account aggregation, investment advice, and tax filing automation are out of initial release scope.
- Any real bank credentials or real financial data are out of scope for public fixtures.

## Install And Test Commands

```powershell
python -m pip install -e .[test]
python -m pytest -q
python -m phantom_finance.cli --help
python -m phantom_finance.cli import .\tests\fixtures\bank_en.csv --account cathay
python -m phantom_finance.cli budget set dining 600
python -m phantom_finance.cli summary --month 2026-06 --json --out .\summary-2026-06.json
python -m phantom_finance.cli scenario-demo --out .\subscription-scenario
python -m phantom_finance.cli planning-scenario --out .\planning-scenario
python -m phantom_finance.cli report --month 2026-06
python -m phantom_finance.cli net-worth
```

Observed result on 2026-06-26:

```text
python -m pytest tests/test_monthly_summary_contract.py tests/test_open_source_contract.py tests/test_tax_report.py tests/test_ingest.py tests/test_budget.py tests/test_reporter.py tests/test_networth.py tests/test_networth_cli.py tests/test_user_rules.py tests/test_correction_rule.py -q: 58 passed
python -m pytest tests/test_subscription_scenario_contract.py tests/test_open_source_contract.py tests/test_monthly_summary_contract.py tests/test_recurring.py tests/test_reporter.py tests/test_budget.py tests/test_networth.py tests/test_networth_cli.py tests/test_user_rules.py tests/test_correction_rule.py -q: 55 passed
python -m pytest tests/test_planning_scenario_contract.py -q: 3 passed
python -m pytest tests/test_planning_scenario_contract.py tests/test_subscription_scenario_contract.py tests/test_open_source_contract.py tests/test_monthly_summary_contract.py tests/test_recurring.py tests/test_reporter.py tests/test_budget.py tests/test_networth.py tests/test_networth_cli.py tests/test_user_rules.py tests/test_correction_rule.py -q: 59 passed
python -m pytest -q: 118 passed in 0.77s
python -m pytest --collect-only -q: 118 tests collected
```

## Fixture And Data Policy

- Public examples must use synthetic bank-like CSV and synthetic ledger data only.
- Ledger JSONL, rule schema, CSV mapping, local account/budget/rate config, and monthly summary artifact schema are documented in `docs/LEDGER_AND_SUMMARY_CONTRACT.md`.
- No real account numbers, credit card details, or private financial records may be committed.
- Monthly summary artifacts are aggregate only and must omit raw transaction rows and descriptions.
- Subscription/scenario artifacts are synthetic-only and must omit raw transaction rows, account numbers, card numbers, private statement lines, and bank credentials.
- Scenario projections are arithmetic what-ifs only and must not be presented as financial advice.
- Planning scenario artifacts are synthetic-only, aggregate-only, and must omit raw transaction rows while keeping live aggregation, external network, and cloud LLM disabled.
- Summary schema version 1 documents its single-currency / already-normalized assumption for income, expense, net, and category totals.

## Safety And Privacy Risks

- Reports can expose sensitive financial behavior if run on real user data.
- LLM-assisted classification, if present, must remain optional and must not send private finance data by default.
- Public docs must state that this is not financial advice.

## Blockers To Next Phase

- None for the current P3 recurring/net-worth planning scenario proof slice.
- Remaining P3 work before Beta sign-off: broader account model ergonomics and goal configuration beyond the fixed synthetic scenario, without adding live account aggregation.

## Evidence

- `pyproject.toml` declares package `phantom-finance` and script `phantom-finance`.
- `README.md` points to `docs/phantom-finance.md`.
- `README.md` includes isolated synthetic quickstart and states this is not financial advice.
- `docs/PUBLIC_DEMO.md` documents synthetic-only public demos and local optional mesh event emission.
- `docs/LEDGER_AND_SUMMARY_CONTRACT.md` documents ledger/config/CSV/summary schemas and aggregate-only privacy boundary.
- `docs/SUBSCRIPTION_AND_SCENARIO_CONTRACT.md` documents scenario-demo, manifest/subscriptions/scenario schemas, synthetic-only policy, no-live-account boundary, and no-advice disclaimer.
- `docs/PLANNING_SCENARIO_PROOF.md` documents planning-scenario, manifest/subscriptions/finance-scenario schemas, recurring/net-worth/runway/savings-goal scenario semantics, synthetic-only policy, and no-advice boundary.
- `python -m pytest tests/test_monthly_summary_contract.py tests/test_open_source_contract.py -q`: 5 passed.
- `python -m pytest tests/test_monthly_summary_contract.py tests/test_open_source_contract.py tests/test_tax_report.py tests/test_ingest.py tests/test_budget.py tests/test_reporter.py tests/test_networth.py tests/test_networth_cli.py tests/test_user_rules.py tests/test_correction_rule.py -q`: 58 passed.
- `python -m pytest tests/test_subscription_scenario_contract.py tests/test_open_source_contract.py tests/test_monthly_summary_contract.py tests/test_recurring.py tests/test_reporter.py tests/test_budget.py tests/test_networth.py tests/test_networth_cli.py tests/test_user_rules.py tests/test_correction_rule.py -q`: 55 passed.
- `python -m pytest tests/test_planning_scenario_contract.py -q`: 3 passed.
- `python -m pytest tests/test_planning_scenario_contract.py tests/test_subscription_scenario_contract.py tests/test_open_source_contract.py tests/test_monthly_summary_contract.py tests/test_recurring.py tests/test_reporter.py tests/test_budget.py tests/test_networth.py tests/test_networth_cli.py tests/test_user_rules.py tests/test_correction_rule.py -q`: 59 passed.
- `python -m pytest -q`: 118 passed.
- `python -m pytest --collect-only -q`: 118 tests collected.
- `python -m phantom_finance.cli --help`: help OK.
- Isolated smoke with `PHANTOM_MESH_HOME=<temp>` and `PHANTOM_FINANCE_HOME=<temp>`:
  - `account add cathay --type cash`: OK.
  - `import .\tests\fixtures\bank_en.csv --account cathay`: imported 3 synthetic transactions.
  - `recat Starbucks dining`: learned local rule.
  - `budget set dining 600` and `budget show --month 2026-06`: dining 150.50 / 600, ok.
  - `summary --month 2026-06 --json --out <temp>\summary-2026-06.json`: wrote schema version 1 aggregate-only JSON, 3 transactions, net 48649.50, no `transactions` field and no raw Starbucks description.
  - `report --month 2026-06`: wrote report under isolated mesh logs.
  - `net-worth`: net worth and spendable cash both 48649.50 TWD.
- `python -m phantom_finance.cli scenario-demo --out <temp>`: wrote schema version 1 `manifest.json`, `subscriptions.json`, `scenario.json`, and `summary.md`; manifest recorded `synthetic_only=true`, `live_account_aggregation=false`, `bank_credentials_required=false`, `financial_advice=false`, `external_network=false`, and `cloud_llm=false`; scenario artifact recorded subscription_count 3, subscription_latest_total 1970, and no raw transaction rows.
- `python -m phantom_finance.cli planning-scenario --out <temp>`: wrote schema version 1 `manifest.json`, `subscriptions.json`, `finance-scenario.json`, and `summary.md`; manifest recorded `synthetic_only=true`, `live_account_aggregation=false`, `bank_credentials_required=false`, `financial_advice=false`, `external_network=false`, and `cloud_llm=false`; finance scenario recorded monthly net 42030, net worth 186210, runway 23.36 months, subscription share 24.72%, and savings-goal baseline/pause-largest-subscription paths without raw transaction rows.
- `agy` reviewer result: no blocking issues. Follow-ups addressed by documenting mixed-currency summary limits and adding the quarter roll-up `非稅務建議` disclaimer/test.
- `agy` P2 subscription/scenario reviewer result: no blockers for recurring income handling, raw transaction leakage, live aggregation/credential implication, financial-advice drift, determinism, CLI/help mismatch, or docs/tests mismatch; low test assertion gap for `external_network=false` and `cloud_llm=false` was fixed.
- `agy` P3 planning scenario reviewer result: initial docs/schema mismatch in `docs/PLANNING_SCENARIO_PROOF.md` was fixed; re-review found `NO BLOCKERS` for privacy leakage, financial-advice drift, live aggregation/credential implication, network/cloud LLM claims, determinism, docs/tests mismatch, or `scenario-demo` regression.

## P4 Release-Prep Slice 1

Status: governance baseline added; this does not mark the project release-ready.

Evidence:
- `CONTRIBUTING.md` defines the contribution workflow, required test command, readiness-doc update rule, and no-private-data/no-credentials boundary.
- `SECURITY.md` defines private vulnerability reporting, supported version scope, 7-day acknowledgement target, and safe report contents.
- `python -m pytest tests/test_release_prep_contract.py -q`: 1 passed.
- `python -m pytest -q`: 119 passed.

Remaining P4 work: full release gate, final docs audit, package metadata audit, release notes, tag plan, and maintainer sign-off.

## P4 Release-Prep Slice 2

Status: final release gate checklist added; this does not mark the project release-ready.

Evidence:
- `CHANGELOG.md` records the unreleased governance/release-checklist work and points back to readiness evidence.
- `docs/RELEASE_CHECKLIST.md` documents final tests, dependency/license review, secret/private-data scan, known limitations, and manual maintainer approval.
- `python -m pytest tests/test_release_prep_contract.py -q`: 2 passed.
- `python -m pytest -q`: 120 passed.

Remaining P4 work: execute final scans, complete dependency/license review, finalize release notes, and record manual maintainer approval.

## P4 Release-Prep Slice 3

Status: final scan and direct dependency/license audit recorded; not release-ready.

Evidence:
- `docs/FINAL_RELEASE_AUDIT.md` records scan scope, `high_conf_secret_hits=0`, direct dependency/license review, and remaining release blockers.
- Direct release-scope dependency review: no runtime dependencies beyond Python stdlib.
- `python -m pytest tests/test_release_prep_contract.py -q`: 3 passed.
- `python -m pytest -q`: 121 passed.

Remaining P4 work: release notes finalization, tag plan, and final maintainer approval.

## P4 Release-Prep Slice 4

Status: maintainer approval recorded, conductor sign-off complete, and release-candidate tag created.

Evidence:
- `docs/RELEASE_NOTES.md` records public release-candidate notes, known limitations, and verification pointers.
- `docs/TAG_PLAN.md` records proposed tag `v0.1.0-alpha.0`, required approval-before-tag sequence, and rollback steps.
- `docs/PUBLIC_RELEASE_APPROVAL.md` records `Status: approved` with approver, approval date, and approved tag.
- Conductor root approval packet `PHANTOM-SATELLITES-PUBLIC-RELEASE-APPROVAL.md` records all ten candidate tags as approved.
- `.github/workflows/ci.yml` runs an explicit `release-prep gate` against `tests/test_release_prep_contract.py`.
- `python -m pytest tests/test_release_prep_contract.py -q`: 5 passed.
- `python -m pytest -q`: 123 passed.

Remaining P4 work: none for the approved release-candidate tag.

## P4 Release-Prep Slice 5

Status: current release-candidate verification refreshed for package metadata, CI, wheel, lint, deterministic smoke, and secret scan.

Evidence:
- `pyproject.toml` declares Apache-2.0 metadata, Python classifiers, project URLs, and `test`/`dev` extras.
- `.github/workflows/ci.yml` installs `.[dev]`, builds a wheel, runs `ruff`, runs the full test suite, runs deterministic public smoke commands, and runs the release-prep gate.
- `tests/test_packaging.py` verifies package metadata and the `phantom-finance` CLI entrypoint target.
- `tests/test_release_prep_contract.py` verifies CI release gates and current audit evidence.
- `python -m pip install -e . --dry-run --no-deps`: passed; would install `phantom-finance-0.1.0a0`.
- `python -m pip wheel . --no-deps -w <temp>`: passed; built `phantom_finance-0.1.0a0-py3-none-any.whl`.
- `python -m phantom_finance.cli --help`: passed.
- Deterministic smoke with isolated `PHANTOM_MESH_HOME` and `PHANTOM_FINANCE_HOME`: summary, `scenario-demo`, and `planning-scenario` artifacts recorded synthetic-only/no-live/no-network/no-cloud-LLM boundaries.
- `python -m ruff check .`: passed; all checks passed.
- `python -m pytest -q`: passed; 126 tests passed.
- Root `python .\run_phantom_satellite_usage_smoke.py`: passed; 10/10 projects OK.
- Root `python .\run_phantom_agent_compat_smoke.py`: passed; 40/40 invocations OK.
- Root `python -m pytest .\tests -q`: passed; 85 tests passed.
- High-confidence secret scan: `high_conf_secret_hits=0`.

Remaining P4 work: none for this public source release candidate.
