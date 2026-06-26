"""Monthly markdown report — shame-free by construction, like phantom-companion.

Numbers are stated, never judged: "over plan" is a fact, "you overspent again"
is shaming and structurally impossible here (no such templates exist).
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

from . import budget, events, ledger, networth, paths, recurring, taxcat
from .ledger import Transaction

SUMMARY_SCHEMA_VERSION = 1


def month_summary(txns: list[Transaction], month: str) -> dict:
    in_month = [t for t in txns if t.month == month and t.category != "transfer"]
    income = sum((t.amount for t in in_month if t.amount > 0), Decimal(0))
    expense = sum((-t.amount for t in in_month if t.amount < 0), Decimal(0))
    by_cat = budget.spend_by_category(txns, month)
    top = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "month": month,
        "txn_count": len(in_month),
        "income": income,
        "expense": expense,
        "net": income - expense,
        "by_category": top,
    }


def monthly_summary_artifact(
    txns: list[Transaction],
    month: str,
    base_currency: str = "TWD",
) -> dict:
    """Aggregate-only machine-readable monthly summary.

    This intentionally omits transaction descriptions and raw rows. It is safe
    for local automation and tests while keeping financial detail in the ledger.
    """
    s = month_summary(txns, month)
    statuses = budget.check(txns, month)
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "month": month,
        "currency": base_currency,
        "transaction_count": s["txn_count"],
        "income": str(s["income"]),
        "expense": str(s["expense"]),
        "net": str(s["net"]),
        "net_worth": str(networth.net_worth(txns, base_currency)),
        "spendable_cash": str(networth.cashflow_total(txns, base_currency)),
        "by_category": [
            {"category": cat, "amount": str(amount)}
            for cat, amount in s["by_category"]
        ],
        "budgets": [
            {
                "category": st.category,
                "spent": str(st.spent),
                "limit": str(st.limit),
                "ratio": round(st.ratio, 4),
                "over": st.over,
            }
            for st in statuses
        ],
    }


def render_summary_text(payload: dict) -> str:
    lines = [
        f"month: {payload['month']}",
        f"transactions: {payload['transaction_count']}",
        f"income: {payload['income']} {payload['currency']}",
        f"expense: {payload['expense']} {payload['currency']}",
        f"net: {payload['net']} {payload['currency']}",
        f"net worth: {payload['net_worth']} {payload['currency']}",
        f"spendable cash: {payload['spendable_cash']} {payload['currency']}",
    ]
    if payload["by_category"]:
        lines.append("by category:")
        for row in payload["by_category"]:
            lines.append(f"- {row['category']}: {row['amount']}")
    if payload["budgets"]:
        lines.append("budgets:")
        for row in payload["budgets"]:
            mark = "over plan" if row["over"] else "ok"
            lines.append(
                f"- {row['category']}: {row['spent']} / {row['limit']} "
                f"({row['ratio']:.0%}) {mark}"
            )
    return "\n".join(lines)


def write_summary_artifact(payload: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


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


def render(txns: list[Transaction], month: str) -> str:
    s = month_summary(txns, month)
    statuses = budget.check(txns, month)
    hikes = recurring.price_hikes(txns)
    lines = [
        f"# phantom-finance · {month}",
        "",
        f"- transactions: {s['txn_count']}",
        f"- income: {s['income']}",
        f"- expense: {s['expense']}",
        f"- net: {s['net']}",
        f"- net worth: {networth.net_worth(txns)}",
        f"- spendable cash: {networth.cashflow_total(txns)}",
        "",
        "## Spending by category",
        "",
    ]
    if s["by_category"]:
        for cat, amount in s["by_category"]:
            lines.append(f"- {cat}: {amount}")
    else:
        lines.append("- (no expenses recorded this month)")
    if statuses:
        lines += ["", "## Budgets", ""]
        for st in statuses:
            mark = "over plan — worth a look" if st.over else "within plan"
            lines.append(
                f"- {st.category}: {st.spent} / {st.limit} ({st.ratio:.0%}) — {mark}"
            )
    if hikes:
        lines += ["", "## Subscription price changes", ""]
        for h in hikes:
            lines.append(
                f"- {h.merchant} ({h.cadence}): now {h.latest_amount}, up "
                f"{h.pct_change:.0f}% — worth a look when you have a moment"
            )
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
    lines += [
        "",
        "_Numbers are observations, not judgements. Adjust the plan, not yourself._",
        "",
    ]
    return "\n".join(lines)


def quarter_months(quarter: str) -> list[str]:
    """'2026Q2' -> ['2026-04','2026-05','2026-06']."""
    norm = quarter.upper().strip()
    if not re.fullmatch(r"\d{4}Q[1-4]", norm):
        raise ValueError(f"bad quarter {quarter!r}, expected e.g. 2026Q2")
    year, q = norm.split("Q")
    first = (int(q) - 1) * 3 + 1
    return [f"{year}-{first + i:02d}" for i in range(3)]


def quarter_tax_summary(txns: list[Transaction], quarter: str) -> dict:
    """Quarter-LEVEL tax roll-up (spec §4 P1): sums across all three months so the
    operator / 記帳士 sees the quarter total no single monthly section shows."""
    months = set(quarter_months(quarter))
    in_quarter = [t for t in txns if t.month in months]
    income_by_type: dict[str, Decimal] = {}
    deductible_total = Decimal(0)
    nhi = 0
    withholding = 0
    for t in in_quarter:
        info = taxcat.classify(t)
        if info.income_type:
            income_by_type[info.income_type] = (
                income_by_type.get(info.income_type, Decimal(0)) + t.amount
            )
        if info.deductible_candidate:
            deductible_total += -t.amount
        if info.nhi_supplement_flag:
            nhi += 1
        if info.withholding_flag:
            withholding += 1
    return {
        "income_by_type": income_by_type,
        "deductible_total": deductible_total,
        "nhi_supplement_count": nhi,
        "withholding_count": withholding,
    }


def render_quarter(txns: list[Transaction], quarter: str) -> str:
    months = quarter_months(quarter)
    qtxns = [t for t in txns if t.month in months]
    qtax = quarter_tax_summary(qtxns, quarter)
    parts = [f"# phantom-finance · {quarter} (季報)", ""]
    # Quarter-level roll-up FIRST: 本季收入/可扣抵/應留意 彙整 across the whole quarter.
    parts += ["## 本季彙整 (quarter roll-up · 非稅務建議)", ""]
    if qtax["income_by_type"]:
        for itype, amount in sorted(qtax["income_by_type"].items()):
            parts.append(f"- 收入 {itype}: {amount}")
    else:
        parts.append("- (本季無收入交易)")
    parts.append(f"- 可扣抵候選合計: {qtax['deductible_total']}")
    if qtax["nhi_supplement_count"]:
        parts.append(
            f"- 二代健保補充保費旗標: {qtax['nhi_supplement_count']} 筆單筆收入 ≥ NT$20,000(需核對)"
        )
    if qtax["withholding_count"]:
        parts.append(
            f"- 扣繳旗標: {qtax['withholding_count']} 筆 9A 收入(請核對是否已預扣 10%)"
        )
    parts.append("")
    for m in months:
        parts.append(render(qtxns, m))
        parts.append("")
    return "\n".join(parts)


def write_quarter_report(quarter: str, txns: list[Transaction] | None = None) -> Path:
    txns = ledger.load() if txns is None else txns
    out = paths.reports_dir() / f"{quarter}-report.md"
    out.write_text(render_quarter(txns, quarter), encoding="utf-8")
    return out


def write_report(month: str, txns: list[Transaction] | None = None) -> Path:
    txns = ledger.load() if txns is None else txns
    out = paths.reports_dir() / f"{month}-report.md"
    out.write_text(render(txns, month), encoding="utf-8")
    s = month_summary(txns, month)
    hikes = recurring.price_hikes(txns)
    tax = tax_summary(txns, month)
    events.emit(
        "monthly-report",
        {
            "month": month,
            "income": str(s["income"]),
            "expense": str(s["expense"]),
            "net": str(s["net"]),
            "income_by_tax_type": {k: str(v) for k, v in tax["income_by_type"].items()},
            "nhi_supplement_count": tax["nhi_supplement_count"],
            "report_path": str(out),
            "price_hikes": [
                {
                    "merchant": h.merchant,
                    "cadence": h.cadence,
                    "latest_amount": str(h.latest_amount),
                    "pct_change": round(h.pct_change),
                }
                for h in hikes
            ],
        },
    )
    return out
