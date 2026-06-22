# phantom-finance Phase 1 (B+A 接案族核心) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-aim the existing phantom-finance pipeline at Taiwan freelancers / 一人公司 — add a correction→rule learning categorizer and a freelancer tax-vocabulary report — all deterministic and offline (no AI/mesh required to work).

**Architecture:** Extend the mature `ingest→categorize→report→emit` pipeline, do NOT rebuild. Two new capabilities: (1) `categorize.py` learns a reusable rule from every manual correction and persists it to the human-readable `rules.json`; (2) a new pure `taxcat.py` module maps each transaction to TW tax fields (9A/9B/salary income split, deductible candidate, 二代健保 / withholding flags), which `reporter.py` surfaces in a "報稅摘要" section + the mesh event. Tax logic is rules + swappable config, never LLM ("報稅前整理", not advice).

**Tech Stack:** Python ≥3.10, stdlib-only (`Decimal`, `json`, `dataclasses`, `argparse`), pytest. Tests use the `isolated_home` autouse fixture in `tests/conftest.py` (each test gets its own `~/.phantom-mesh`) and `paths.rules_path()` / `paths.ledger_path()`.

**Spec:** `docs/specs/2026-06-22-b-plus-a-positioning-design.md` (Phase 1 = §4 Phase 1 + §5 centerpiece).

---

## File Structure

- **Modify** `phantom_finance/categorize.py` — add `derive_keyword(description)` + `add_user_rule(keyword, category, path=None)` (the rule deriver/writer; today the module only READS rules).
- **Modify** `phantom_finance/cli.py` — extend the `recat` subcommand with an optional manual-correction mode `recat <match> <category>` (correction → derive rule → persist → backfill); keep the existing no-arg "re-run on uncategorized" mode.
- **Create** `phantom_finance/taxcat.py` — pure, deterministic TW tax classifier (`TaxInfo` + `classify(txn)`), config-driven (swappable for other jurisdictions later).
- **Modify** `phantom_finance/reporter.py` — add `tax_summary(txns, month)` + a "## 報稅摘要 (tax prep)" section in `render()` + tax fields in the emitted event; add `quarter_summary` + quarterly report.
- **Create** tests: `tests/test_correction_rule.py`, `tests/test_taxcat.py`, `tests/test_tax_report.py`.

Run all tests with: `python -m pytest -q` (repo uses system python via `pip install -e .`; no venv required).

---

### Task 1: Rule deriver + writer in `categorize.py`

**Files:**
- Modify: `phantom_finance/categorize.py`
- Test: `tests/test_correction_rule.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_correction_rule.py
import json
from decimal import Decimal

from phantom_finance import categorize, paths
from phantom_finance.ledger import Transaction


def txn(desc: str, amount: str = "-100") -> Transaction:
    return Transaction(date="2026-06-01", amount=Decimal(amount), description=desc)


def test_derive_keyword_lowercases_and_trims():
    # a noisy bank description collapses to a stable, reusable keyword
    assert categorize.derive_keyword("  路邊滷味攤 #1234 ") == "路邊滷味攤 #1234"
    assert categorize.derive_keyword("STARBUCKS XINYI A1") == "starbucks xinyi a1"


def test_add_user_rule_creates_human_readable_json():
    categorize.add_user_rule("路邊滷味攤", "street-food")
    data = json.loads(paths.rules_path().read_text(encoding="utf-8"))
    assert data == {"路邊滷味攤": "street-food"}
    # round-trips through the existing loader
    assert categorize.load_user_rules()["路邊滷味攤"] == "street-food"


def test_add_user_rule_merges_without_clobbering_existing():
    paths.rules_path().write_text('{"全聯": "groceries"}', encoding="utf-8")
    categorize.add_user_rule("foodpanda", "delivery")
    data = json.loads(paths.rules_path().read_text(encoding="utf-8"))
    assert data == {"全聯": "groceries", "foodpanda": "delivery"}


def test_added_rule_is_used_by_categorizer():
    categorize.add_user_rule("某神秘商店", "shopping")
    assert categorize.categorize_one(txn("某神秘商店 信義店")) == "shopping"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_correction_rule.py -v`
Expected: FAIL with `AttributeError: module 'phantom_finance.categorize' has no attribute 'derive_keyword'`

- [ ] **Step 3: Write minimal implementation**

Add to `phantom_finance/categorize.py` (after `load_user_rules`, before `effective_rules`):

```python
def derive_keyword(description: str) -> str:
    """Turn a raw transaction description into a stable, reusable rule keyword.

    Rules match by lowercase substring (see categorize_one), so the keyword is
    the lowercased, whitespace-collapsed description. Kept deliberately simple:
    a human can edit rules.json afterwards to broaden/narrow the match.
    """
    return " ".join(description.split()).lower()


def add_user_rule(keyword: str, category: str, path: Path | None = None) -> None:
    """Persist a single keyword->category rule to the user rules file (merge, not
    clobber). Written as pretty UTF-8 JSON so it stays human-readable + editable."""
    p = path or paths.rules_path()
    rules = load_user_rules(p)
    rules[keyword.strip().lower()] = category
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_correction_rule.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add phantom_finance/categorize.py tests/test_correction_rule.py
git commit -m "feat(categorize): derive_keyword + add_user_rule (rule writer)"
```

---

### Task 2: `recat <match> <category>` manual correction → learns a rule

**Files:**
- Modify: `phantom_finance/cli.py` (parser at line ~66 `sub.add_parser("recat", ...)`; handler at line ~130 `elif args.cmd == "recat":`)
- Test: `tests/test_correction_rule.py` (append)

- [ ] **Step 1: Write the failing test (append to tests/test_correction_rule.py)**

```python
from phantom_finance import cli, ledger


def test_recat_manual_correction_persists_rule_and_backfills():
    # two txns from the same merchant land uncategorized
    ledger.append([
        Transaction(date="2026-06-01", amount=Decimal("-250"), description="路邊滷味攤 信義"),
        Transaction(date="2026-06-09", amount=Decimal("-300"), description="路邊滷味攤 大安"),
    ])
    # operator corrects ONE: recat <match> <category>
    rc = cli.main(["recat", "路邊滷味攤", "street-food"])
    assert rc == 0
    # both existing txns are backfilled
    cats = {t.category for t in ledger.load()}
    assert cats == {"street-food"}
    # the correction became a durable rule
    assert categorize.load_user_rules()["路邊滷味攤"] == "street-food"


def test_recat_learned_rule_categorizes_future_import_offline():
    cli.main(["recat", "路邊滷味攤", "street-food"])
    # a NEW transaction from the same merchant, categorized with NO llm
    t = Transaction(date="2026-07-02", amount=Decimal("-180"), description="路邊滷味攤 內湖")
    assert categorize.categorize_one(t, llm=None) == "street-food"


def test_recat_no_args_still_reruns_uncategorized():
    ledger.append([Transaction(date="2026-06-01", amount=Decimal("-100"), description="全聯 週末")])
    rc = cli.main(["recat"])
    assert rc == 0
    assert ledger.load()[0].category == "groceries"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_correction_rule.py -k recat -v`
Expected: FAIL — `recat` does not accept positionals yet (argparse error / SystemExit), and no backfill.

- [ ] **Step 3: Update the parser**

In `phantom_finance/cli.py`, replace the line:

```python
    sub.add_parser("recat", help="re-run the categorizer on uncategorized txns")
```

with:

```python
    p_recat = sub.add_parser(
        "recat",
        help="re-categorize; with MATCH CATEGORY, correct + learn a durable rule",
    )
    p_recat.add_argument("match", nargs="?", help="substring of the description to correct")
    p_recat.add_argument("category", nargs="?", help="category to assign + remember")
```

- [ ] **Step 4: Update the handler**

In `phantom_finance/cli.py`, replace the block:

```python
    elif args.cmd == "recat":
        txns = ledger.load()
        changed = categorize.apply(txns, llm=llm.make_categorizer())
        ledger.rewrite(txns)
        print(f"re-categorized {changed} transactions")
```

with:

```python
    elif args.cmd == "recat":
        txns = ledger.load()
        if args.match and args.category:
            # manual correction: learn a durable rule, then backfill every match
            keyword = categorize.derive_keyword(args.match)
            categorize.add_user_rule(keyword, args.category)
            changed = 0
            for t in txns:
                if keyword in t.description.lower() and t.category != args.category:
                    t.category = args.category
                    changed += 1
            ledger.rewrite(txns)
            print(f"learned rule {keyword!r} -> {args.category}; backfilled {changed} txns")
        elif args.match or args.category:
            print("usage: phantom-finance recat [MATCH CATEGORY]", file=sys.stderr)
            return 2
        else:
            changed = categorize.apply(txns, llm=llm.make_categorizer())
            ledger.rewrite(txns)
            print(f"re-categorized {changed} transactions")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_correction_rule.py -v`
Expected: PASS (all)

- [ ] **Step 6: Commit**

```bash
git add phantom_finance/cli.py tests/test_correction_rule.py
git commit -m "feat(cli): recat MATCH CATEGORY learns a durable rule + backfills"
```

---

### Task 3: `taxcat.py` — income-type classification (9A/9B/salary/other)

**Files:**
- Create: `phantom_finance/taxcat.py`
- Test: `tests/test_taxcat.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_taxcat.py
from decimal import Decimal

from phantom_finance import taxcat
from phantom_finance.ledger import Transaction


def inc(desc: str, amount: str) -> Transaction:
    return Transaction(date="2026-06-01", amount=Decimal(amount), description=desc)


def test_freelance_income_classifies_9a():
    assert taxcat.classify(inc("某公司 程式設計 接案款", "30000")).income_type == "9A"
    assert taxcat.classify(inc("顧問費", "15000")).income_type == "9A"


def test_salary_classifies_salary():
    assert taxcat.classify(inc("六月份 薪資", "50000")).income_type == "salary"


def test_royalty_classifies_9b():
    assert taxcat.classify(inc("出版社 版稅", "8000")).income_type == "9B"


def test_dividend_interest_is_other_income():
    assert taxcat.classify(inc("台積電 股息", "5000")).income_type == "other_income"


def test_unknown_income_defaults_to_9a_for_freelancers():
    assert taxcat.classify(inc("某神秘入帳", "12000")).income_type == "9A"


def test_expense_has_no_income_type():
    assert taxcat.classify(inc("全聯", "-500")).income_type is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_taxcat.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'phantom_finance.taxcat'`

- [ ] **Step 3: Write minimal implementation**

```python
# phantom_finance/taxcat.py
"""Deterministic Taiwan tax classification for freelancers / 一人公司.

PHASE-1 SCOPE + SAFETY: this is "報稅前整理" (filing prep), NOT tax advice. Every
mapping is a rule in a swappable config dict (so other jurisdictions can be added
later without touching the engine), and the LLM is never involved in tax/amount
logic. Outputs are clearly "候選 / 待確認" — the operator or their 記帳士 decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .ledger import Transaction

# description keyword (lowercase substring) -> Taiwan income type
INCOME_TYPE_RULES: dict[str, str] = {
    "薪資": "salary", "薪水": "salary", "salary": "salary", "payroll": "salary",
    "稿費": "9A", "演講": "9A", "授課": "9A", "鐘點": "9A", "設計": "9A",
    "程式": "9A", "開發": "9A", "顧問": "9A", "接案": "9A", "外包": "9A",
    "freelance": "9A", "consult": "9A", "translation": "9A", "翻譯": "9A",
    "版稅": "9B", "權利金": "9B", "royalty": "9B",
    "股息": "other_income", "股利": "other_income", "dividend": "other_income",
    "利息": "other_income", "interest": "other_income",
}
# 接案族 default: unknown professional income is a 9A candidate (most common case)
DEFAULT_INCOME_TYPE = "9A"


@dataclass(frozen=True)
class TaxInfo:
    income_type: str | None  # "9A"|"9B"|"salary"|"other_income" for income; None for expenses
    deductible_candidate: bool
    nhi_supplement_flag: bool
    withholding_flag: bool


def _income_type(description: str) -> str:
    desc = description.lower()
    for keyword, itype in INCOME_TYPE_RULES.items():
        if keyword in desc:
            return itype
    return DEFAULT_INCOME_TYPE


def classify(txn: Transaction) -> TaxInfo:
    if txn.amount > 0:
        itype = _income_type(txn.description)
        return TaxInfo(
            income_type=itype,
            deductible_candidate=False,
            nhi_supplement_flag=False,  # filled in Task 4
            withholding_flag=False,     # filled in Task 4
        )
    return TaxInfo(
        income_type=None,
        deductible_candidate=False,  # filled in Task 4
        nhi_supplement_flag=False,
        withholding_flag=False,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_taxcat.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add phantom_finance/taxcat.py tests/test_taxcat.py
git commit -m "feat(taxcat): TW income-type classification (9A/9B/salary/other)"
```

---

### Task 4: `taxcat.py` — deductible candidate + 二代健保 + withholding flags

**Files:**
- Modify: `phantom_finance/taxcat.py`
- Test: `tests/test_taxcat.py` (append)

- [ ] **Step 1: Write the failing test (append)**

```python
def test_business_category_expense_is_deductible_candidate():
    t = inc("中華電信 網路費", "-899")
    t.category = "utilities"
    assert taxcat.classify(t).deductible_candidate is True


def test_personal_category_expense_is_not_deductible():
    t = inc("星巴克", "-160")
    t.category = "dining"
    assert taxcat.classify(t).deductible_candidate is False


def test_large_single_income_flags_nhi_supplement():
    # single payment >= NT$20,000 triggers 二代健保補充保費 (2.11%)
    assert taxcat.classify(inc("接案款", "20000")).nhi_supplement_flag is True
    assert taxcat.classify(inc("接案款", "19999")).nhi_supplement_flag is False


def test_9a_income_flags_withholding():
    assert taxcat.classify(inc("顧問費", "30000")).withholding_flag is True
    # salary / other income are not 9A withholding
    assert taxcat.classify(inc("薪資", "50000")).withholding_flag is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_taxcat.py -k "deductible or nhi or withholding" -v`
Expected: FAIL — flags are hardcoded False.

- [ ] **Step 3: Update the implementation**

In `phantom_finance/taxcat.py`, add config near the top (after `DEFAULT_INCOME_TYPE`):

```python
# expense categories (from categorize.py) that MIGHT be business-deductible.
# "candidate" only — the operator / 記帳士 confirms; never auto-claimed.
DEDUCTIBLE_CANDIDATE_CATEGORIES: set[str] = {
    "utilities", "transport", "subscription", "equipment", "software", "office",
}
# single income payment at/above this triggers 二代健保補充保費 (2.11%)
NHI_SUPPLEMENT_THRESHOLD = Decimal("20000")
```

Then replace the body of `classify` with:

```python
def classify(txn: Transaction) -> TaxInfo:
    if txn.amount > 0:
        itype = _income_type(txn.description)
        return TaxInfo(
            income_type=itype,
            deductible_candidate=False,
            nhi_supplement_flag=txn.amount >= NHI_SUPPLEMENT_THRESHOLD,
            withholding_flag=itype == "9A",
        )
    return TaxInfo(
        income_type=None,
        deductible_candidate=txn.category in DEDUCTIBLE_CANDIDATE_CATEGORIES,
        nhi_supplement_flag=False,
        withholding_flag=False,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_taxcat.py -v`
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add phantom_finance/taxcat.py tests/test_taxcat.py
git commit -m "feat(taxcat): deductible-candidate + 二代健保 + withholding flags"
```

---

### Task 5: `reporter.py` — 報稅摘要 section + tax fields in the event

**Files:**
- Modify: `phantom_finance/reporter.py`
- Test: `tests/test_tax_report.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tax_report.py
from decimal import Decimal

from phantom_finance import reporter
from phantom_finance.ledger import Transaction


def _txns():
    return [
        Transaction(date="2026-06-03", amount=Decimal("30000"), description="A公司 程式接案", category="income"),
        Transaction(date="2026-06-10", amount=Decimal("8000"), description="出版社 版稅", category="income"),
        Transaction(date="2026-06-12", amount=Decimal("-899"), description="中華電信", category="utilities"),
        Transaction(date="2026-06-15", amount=Decimal("-160"), description="星巴克", category="dining"),
    ]


def test_tax_summary_splits_income_by_type():
    s = reporter.tax_summary(_txns(), "2026-06")
    assert s["income_by_type"]["9A"] == Decimal("30000")
    assert s["income_by_type"]["9B"] == Decimal("8000")
    assert Decimal("899") in [amt for _, amt in s["deductible_candidates"]]
    assert s["nhi_supplement_count"] == 1  # the 30000 9A payment


def test_render_includes_tax_section():
    md = reporter.render(_txns(), "2026-06")
    assert "報稅摘要" in md
    assert "9A" in md
    assert "可扣抵候選" in md
    # safety: it is prep, not advice
    assert "非稅務建議" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_tax_report.py -v`
Expected: FAIL — `reporter` has no `tax_summary`; `render` has no 報稅摘要 section.

- [ ] **Step 3: Add `tax_summary` and extend `render`**

In `phantom_finance/reporter.py`, add `from . import taxcat` to the imports, then add this function above `render`:

```python
def tax_summary(txns: list[Transaction], month: str) -> dict:
    in_month = [t for t in txns if t.month == month]
    income_by_type: dict[str, Decimal] = {}
    deductible: list[tuple[str, Decimal]] = []
    nhi = 0
    withholding = 0
    for t in in_month:
        info = taxcat.classify(t)
        if info.income_type:
            income_by_type[info.income_type] = (
                income_by_type.get(info.income_type, Decimal(0)) + t.amount
            )
        if info.deductible_candidate:
            deductible.append((t.description, -t.amount))
        if info.nhi_supplement_flag:
            nhi += 1
        if info.withholding_flag:
            withholding += 1
    return {
        "income_by_type": income_by_type,
        "deductible_candidates": deductible,
        "nhi_supplement_count": nhi,
        "withholding_count": withholding,
    }
```

Then, in `render`, insert a tax section just before the trailing `lines += ["", "_Numbers are observations..."]` block:

```python
    tax = tax_summary(txns, month)
    lines += ["", "## 報稅摘要 (tax prep · 非稅務建議,給你或你的記帳士核對)", ""]
    if tax["income_by_type"]:
        for itype, amount in sorted(tax["income_by_type"].items()):
            lines.append(f"- 收入 {itype}: {amount}")
    else:
        lines.append("- (本月無收入交易)")
    if tax["deductible_candidates"]:
        lines.append("- 可扣抵候選:")
        for desc, amount in tax["deductible_candidates"]:
            lines.append(f"  - {desc}: {amount}")
    if tax["nhi_supplement_count"]:
        lines.append(
            f"- 二代健保補充保費旗標: {tax['nhi_supplement_count']} 筆單筆收入 ≥ NT$20,000(需核對)"
        )
    if tax["withholding_count"]:
        lines.append(
            f"- 扣繳旗標: {tax['withholding_count']} 筆 9A 收入(請核對是否已預扣 10%)"
        )
```

- [ ] **Step 4: Add the tax block to the emitted event**

In `write_report`, inside the `events.emit("monthly-report", {...})` payload dict, add (after `"net": str(s["net"]),`):

```python
            "income_by_tax_type": {k: str(v) for k, v in tax_summary(txns, month)["income_by_type"].items()},
            "nhi_supplement_count": tax_summary(txns, month)["nhi_supplement_count"],
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_tax_report.py tests/test_reporter.py tests/test_price_hike_report.py -v`
Expected: PASS (new tax tests pass; existing reporter tests still green)

- [ ] **Step 6: Commit**

```bash
git add phantom_finance/reporter.py tests/test_tax_report.py
git commit -m "feat(reporter): 報稅摘要 section + tax fields in monthly event"
```

---

### Task 6: Quarterly report (`report --quarter YYYYQn`)

**Files:**
- Modify: `phantom_finance/reporter.py` (add `quarter_months` + `write_quarter_report`)
- Modify: `phantom_finance/cli.py` (report subparser gets `--quarter`; handler branches)
- Test: `tests/test_tax_report.py` (append)

- [ ] **Step 1: Write the failing test (append to tests/test_tax_report.py)**

```python
from phantom_finance import paths


def test_quarter_months_expands_correctly():
    assert reporter.quarter_months("2026Q2") == ["2026-04", "2026-05", "2026-06"]


def test_write_quarter_report_aggregates_three_months(monkeypatch):
    txns = [
        Transaction(date="2026-04-10", amount=Decimal("30000"), description="接案", category="income"),
        Transaction(date="2026-06-10", amount=Decimal("20000"), description="顧問費", category="income"),
    ]
    out = reporter.write_quarter_report("2026Q2", txns=txns)
    assert out.exists()
    body = out.read_text(encoding="utf-8")
    assert "2026Q2" in body
    assert "報稅摘要" in body
    assert "50000" in body  # 9A income aggregated across the quarter
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_tax_report.py -k quarter -v`
Expected: FAIL — no `quarter_months` / `write_quarter_report`.

- [ ] **Step 3: Add quarterly functions to `reporter.py`**

```python
def quarter_months(quarter: str) -> list[str]:
    """'2026Q2' -> ['2026-04','2026-05','2026-06']."""
    year, q = quarter.upper().split("Q")
    first = (int(q) - 1) * 3 + 1
    return [f"{year}-{first + i:02d}" for i in range(3)]


def render_quarter(txns: list[Transaction], quarter: str) -> str:
    months = quarter_months(quarter)
    qtxns = [t for t in txns if t.month in months]
    parts = [f"# phantom-finance · {quarter} (季報)", ""]
    for m in months:
        parts.append(render(qtxns, m))
        parts.append("")
    return "\n".join(parts)


def write_quarter_report(quarter: str, txns: list[Transaction] | None = None) -> Path:
    txns = ledger.load() if txns is None else txns
    out = paths.reports_dir() / f"{quarter}-report.md"
    out.write_text(render_quarter(txns, quarter), encoding="utf-8")
    return out
```

- [ ] **Step 4: Wire the CLI**

In `phantom_finance/cli.py`, the report subparser is created at line ~44 (`p_rep = sub.add_parser("report", ...)`). Add an optional flag to it:

```python
    p_rep.add_argument("--quarter", help="write a quarterly report instead, e.g. 2026Q2")
```

Then replace the `report` handler:

```python
    elif args.cmd == "report":
        out = reporter.write_report(args.month)
        print(f"report written: {out}")
```

with:

```python
    elif args.cmd == "report":
        if getattr(args, "quarter", None):
            out = reporter.write_quarter_report(args.quarter)
        else:
            out = reporter.write_report(args.month)
        print(f"report written: {out}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_tax_report.py -v`
Expected: PASS (all)

- [ ] **Step 6: Commit**

```bash
git add phantom_finance/reporter.py phantom_finance/cli.py tests/test_tax_report.py
git commit -m "feat(reporter,cli): quarterly report (report --quarter YYYYQn)"
```

---

### Task 7: Full-suite verification + done

**Files:** none (verification only)

- [ ] **Step 1: Run the whole suite**

Run: `python -m pytest -q`
Expected: PASS — all pre-existing tests (categorize / ledger / reporter / recurring / networth / presets / user_rules / price_hike / ingest / budget / account_cli / networth_cli / llm) plus the 3 new files (`test_correction_rule`, `test_taxcat`, `test_tax_report`) GREEN, 0 failed.

- [ ] **Step 2: Manual smoke (offline, no AI)**

```bash
python -m phantom_finance.cli add -- 30000 "A公司 程式接案"
python -m phantom_finance.cli add -- -899 "中華電信 網路"
python -m phantom_finance.cli recat 路邊滷味 street-food   # learns a rule even with 0 matches
python -m phantom_finance.cli report --month 2026-06
```
Expected: the report file contains a `## 報稅摘要` section with `收入 9A: 30000`, a `可扣抵候選` line for 中華電信, and the `非稅務建議` safety note.

- [ ] **Step 3: Final commit (if any docs touched) + hand back**

No code change in this task. If green, Phase 1 is complete; Phase 2 (tax wedge: actual-expense vs standard-ratio, 年度報稅包, 載具 ingestion) and Phase 3 (mesh MCP layer) get their own plans.

---

## Self-Review

**Spec coverage (spec §4 Phase 1 + §5):**
- §4 Phase 1 (1) 報告新增稅務語彙欄位 (9A/9B、可扣抵、二代健保/扣繳) → Tasks 3-5 ✅
- §4 Phase 1 (2) 接案族月報 + 季報 → Tasks 5 (月) + 6 (季) ✅
- §5 中心功能 correction→rule 學習引擎 (含驗收條件:更正一次後同商家零人工零 AI 命中、規則檔人類可讀、離線可跑) → Tasks 1-2 ✅ (`test_recat_learned_rule_categorizes_future_import_offline`, `test_add_user_rule_creates_human_readable_json`)
- §2 鐵則「AI 預設 off、稅務規則式」→ taxcat is pure/deterministic, no LLM import; categorizer llm stays optional (Task 2 no-arg path still uses `llm.make_categorizer()` exactly as today) ✅
- §8 風險 2「定位報稅前整理非建議」→ render emits `非稅務建議` note (Task 5 test asserts it) ✅

**Placeholder scan:** No TBD/TODO; every step has runnable code + exact commands. ✅

**Type consistency:** `TaxInfo` fields (`income_type`, `deductible_candidate`, `nhi_supplement_flag`, `withholding_flag`) defined in Task 3, populated in Task 4, consumed in Task 5 `tax_summary` — names match. `derive_keyword`/`add_user_rule` defined in Task 1, used in Task 2 handler — match. `quarter_months`/`write_quarter_report` defined + used in Task 6 — match. ✅

**Out of scope (deferred, per spec):** Phase 2 (執行業務 actual-expense vs standard-ratio, 年度報稅包, 載具/電子發票 ingestion, 憑證歸檔) and Phase 3 (MCP/NL/agent layer) — separate plans.
