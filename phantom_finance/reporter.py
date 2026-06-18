"""Monthly markdown report — shame-free by construction, like phantom-companion.

Numbers are stated, never judged: "over plan" is a fact, "you overspent again"
is shaming and structurally impossible here (no such templates exist).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from . import budget, events, ledger, networth, paths, recurring
from .ledger import Transaction


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
    lines += [
        "",
        "_Numbers are observations, not judgements. Adjust the plan, not yourself._",
        "",
    ]
    return "\n".join(lines)


def write_report(month: str, txns: list[Transaction] | None = None) -> Path:
    txns = ledger.load() if txns is None else txns
    out = paths.reports_dir() / f"{month}-report.md"
    out.write_text(render(txns, month), encoding="utf-8")
    s = month_summary(txns, month)
    hikes = recurring.price_hikes(txns)
    events.emit(
        "monthly-report",
        {
            "month": month,
            "income": str(s["income"]),
            "expense": str(s["expense"]),
            "net": str(s["net"]),
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
