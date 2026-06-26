from __future__ import annotations

import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any

from . import budget, networth, recurring, reporter
from .ledger import Transaction

SCENARIO_SCHEMA_VERSION = 1
PUBLIC_ARTIFACTS = [
    "manifest.json",
    "subscriptions.json",
    "scenario.json",
    "summary.md",
]
PLANNING_SCENARIO_ARTIFACTS = [
    "manifest.json",
    "subscriptions.json",
    "finance-scenario.json",
    "summary.md",
]


def synthetic_subscription_transactions() -> list[Transaction]:
    rows = [
        ("2026-03-01", "50000", "Synthetic Salary", "income"),
        ("2026-04-01", "50000", "Synthetic Salary", "income"),
        ("2026-05-01", "50000", "Synthetic Salary", "income"),
        ("2026-06-01", "50000", "Synthetic Salary", "income"),
        ("2026-03-05", "-390", "StreamFlix", "subscriptions"),
        ("2026-04-05", "-390", "StreamFlix", "subscriptions"),
        ("2026-05-05", "-390", "StreamFlix", "subscriptions"),
        ("2026-06-05", "-420", "StreamFlix", "subscriptions"),
        ("2026-03-07", "-350", "CloudBox", "subscriptions"),
        ("2026-04-07", "-350", "CloudBox", "subscriptions"),
        ("2026-05-07", "-350", "CloudBox", "subscriptions"),
        ("2026-06-07", "-350", "CloudBox", "subscriptions"),
        ("2026-03-10", "-1200", "City Gym", "subscriptions"),
        ("2026-04-10", "-1200", "City Gym", "subscriptions"),
        ("2026-05-10", "-1200", "City Gym", "subscriptions"),
        ("2026-06-10", "-1200", "City Gym", "subscriptions"),
        ("2026-06-12", "-4000", "Synthetic Groceries", "groceries"),
        ("2026-06-15", "-1500", "Synthetic Utilities", "utilities"),
        ("2026-06-20", "-500", "Synthetic Transit", "transport"),
    ]
    return [
        Transaction(
            date=date,
            amount=Decimal(amount),
            description=description,
            account="synthetic",
            category=category,
        )
        for date, amount, description, category in rows
    ]


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("1")) if value == value.to_integral() else value)


def _norm_label(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _ceil_months(gap: Decimal, monthly_net: Decimal) -> int | None:
    if gap <= 0:
        return 0
    if monthly_net <= 0:
        return None
    return int((gap / monthly_net).to_integral_value(rounding=ROUND_CEILING))


def _pct(part: Decimal, whole: Decimal) -> float:
    if whole == 0:
        return 0.0
    return round(float(part / whole * Decimal("100")), 2)


def synthetic_planning_budgets() -> dict[str, Decimal]:
    return {
        "groceries": Decimal("5000"),
        "subscriptions": Decimal("2200"),
        "transport": Decimal("800"),
        "utilities": Decimal("1600"),
    }


def _subscription_rows(txns: list[Transaction]) -> list[dict[str, Any]]:
    expense_labels = {
        _norm_label(txn.description)
        for txn in txns
        if txn.amount < 0
    }
    rows = []
    for charge in recurring.detect(txns):
        if charge.latest_amount <= 0 or _norm_label(charge.merchant) not in expense_labels:
            continue
        rows.append(
            {
                "label": charge.merchant,
                "cadence": charge.cadence,
                "occurrences": charge.occurrences,
                "typical_amount": _money(charge.typical_amount),
                "latest_amount": _money(charge.latest_amount),
                "first_date": charge.first_date,
                "last_date": charge.last_date,
                "price_increased": charge.price_increased,
                "pct_change": round(charge.pct_change, 2),
            }
        )
    return sorted(rows, key=lambda row: (-Decimal(row["latest_amount"]), row["label"]))


def subscription_scenario_artifact(
    txns: list[Transaction],
    *,
    month: str = "2026-06",
    horizon_months: int = 3,
    currency: str = "TWD",
) -> dict[str, Any]:
    summary = reporter.monthly_summary_artifact(txns, month, base_currency=currency)
    subscriptions = _subscription_rows(txns)
    monthly_net = Decimal(summary["net"])
    largest = subscriptions[0] if subscriptions else None
    largest_amount = Decimal(largest["latest_amount"]) if largest else Decimal(0)

    baseline_delta = monthly_net * horizon_months
    pause_delta = (monthly_net + largest_amount) * horizon_months

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "mode": "synthetic_subscription_scenario_loop",
        "data_policy": "synthetic_only",
        "month": month,
        "currency": currency,
        "horizon_months": horizon_months,
        "financial_advice": False,
        "live_account_aggregation": False,
        "bank_credentials_required": False,
        "raw_transaction_rows_included": False,
        "disclaimer": "Arithmetic what-if only; not financial advice.",
        "summary": {
            "month": month,
            "income": summary["income"],
            "expense": summary["expense"],
            "net": summary["net"],
            "subscription_count": len(subscriptions),
            "subscription_latest_total": _money(
                sum((Decimal(row["latest_amount"]) for row in subscriptions), Decimal(0))
            ),
        },
        "scenarios": [
            {
                "name": "baseline",
                "description": "Carry the current synthetic monthly net cashflow forward.",
                "monthly_net": _money(monthly_net),
                "projected_delta": _money(baseline_delta),
            },
            {
                "name": "pause_largest_subscription",
                "description": "Arithmetic delta if the largest synthetic subscription were absent.",
                "affected_subscription": largest["label"] if largest else None,
                "monthly_net": _money(monthly_net + largest_amount),
                "projected_delta": _money(pause_delta),
                "delta_vs_baseline": _money(pause_delta - baseline_delta),
            },
        ],
    }


def subscriptions_artifact(txns: list[Transaction]) -> dict[str, Any]:
    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "mode": "synthetic_subscription_detection",
        "data_policy": "synthetic_only",
        "raw_transaction_rows_included": False,
        "subscriptions": _subscription_rows(txns),
    }


def manifest() -> dict[str, Any]:
    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "mode": "synthetic_subscription_scenario_loop",
        "synthetic_only": True,
        "live_account_aggregation": False,
        "bank_credentials_required": False,
        "financial_advice": False,
        "external_network": False,
        "cloud_llm": False,
        "artifacts": PUBLIC_ARTIFACTS,
    }


def planning_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "mode": "synthetic_finance_planning_scenario",
        "synthetic_only": True,
        "live_account_aggregation": False,
        "bank_credentials_required": False,
        "financial_advice": False,
        "external_network": False,
        "cloud_llm": False,
        "artifacts": PLANNING_SCENARIO_ARTIFACTS,
    }


def finance_planning_scenario_artifact(
    txns: list[Transaction],
    *,
    month: str = "2026-06",
    horizon_months: int = 6,
    savings_goal: Decimal = Decimal("400000"),
    currency: str = "TWD",
) -> dict[str, Any]:
    summary = reporter.monthly_summary_artifact(txns, month, base_currency=currency)
    subscriptions = _subscription_rows(txns)
    budgets = budget.check(txns, month, budgets=synthetic_planning_budgets())

    monthly_net = Decimal(summary["net"])
    monthly_expense = Decimal(summary["expense"])
    nw = networth.net_worth(txns, base=currency, rates={currency: Decimal("1")})
    cash = networth.cashflow_total(
        txns,
        base=currency,
        rates={currency: Decimal("1")},
        account_types={},
    )
    subscription_total = sum(
        (Decimal(row["latest_amount"]) for row in subscriptions),
        Decimal(0),
    )
    largest = subscriptions[0] if subscriptions else None
    largest_amount = Decimal(largest["latest_amount"]) if largest else Decimal(0)
    gap = max(savings_goal - cash, Decimal(0))
    baseline_months = _ceil_months(gap, monthly_net)
    pause_monthly_net = monthly_net + largest_amount
    pause_months = _ceil_months(gap, pause_monthly_net)

    baseline_projected = cash + monthly_net * horizon_months
    pause_projected = cash + pause_monthly_net * horizon_months

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "mode": "synthetic_finance_planning_scenario",
        "data_policy": "synthetic_only",
        "month": month,
        "currency": currency,
        "horizon_months": horizon_months,
        "financial_advice": False,
        "live_account_aggregation": False,
        "bank_credentials_required": False,
        "raw_transaction_rows_included": False,
        "external_network": False,
        "cloud_llm": False,
        "disclaimer": "Arithmetic planning scenario only; not financial advice.",
        "summary": {
            "month": month,
            "monthly_income": summary["income"],
            "monthly_expense": summary["expense"],
            "monthly_net": summary["net"],
            "net_worth": _money(nw),
            "spendable_cash": _money(cash),
            "subscription_count": len(subscriptions),
            "subscription_latest_total": _money(subscription_total),
        },
        "runway": {
            "monthly_expense": summary["expense"],
            "runway_months": round(float(cash / monthly_expense), 2)
            if monthly_expense > 0 else None,
            "subscription_share_of_expense_pct": _pct(subscription_total, monthly_expense),
        },
        "savings_goal": {
            "target_amount": _money(savings_goal),
            "gap": _money(gap),
            "baseline_months_to_goal": baseline_months,
            "pause_largest_subscription_months_to_goal": pause_months,
        },
        "budgets": [
            {
                "category": row.category,
                "spent": _money(row.spent),
                "limit": _money(row.limit),
                "remaining": _money(row.limit - row.spent),
                "ratio": round(row.ratio, 4),
                "over": row.over,
            }
            for row in budgets
        ],
        "scenarios": [
            {
                "name": "baseline_goal_path",
                "description": "Carry the current synthetic monthly net cashflow toward the savings goal.",
                "monthly_net": _money(monthly_net),
                "projected_net_worth": _money(baseline_projected),
                "months_to_goal": baseline_months,
            },
            {
                "name": "pause_largest_subscription_goal_path",
                "description": "Arithmetic delta if the largest synthetic subscription were absent.",
                "affected_subscription": largest["label"] if largest else None,
                "monthly_net": _money(pause_monthly_net),
                "projected_net_worth": _money(pause_projected),
                "months_to_goal": pause_months,
                "delta_vs_baseline": _money(pause_projected - baseline_projected),
            },
        ],
    }


def render_summary(payload: dict[str, Any], subscriptions: dict[str, Any]) -> str:
    lines = [
        "# phantom-finance subscription scenario demo",
        "",
        "Synthetic arithmetic only; not financial advice.",
        "",
        f"- month: {payload['month']}",
        f"- horizon: {payload['horizon_months']} months",
        f"- net: {payload['summary']['net']} {payload['currency']}",
        f"- subscriptions detected: {payload['summary']['subscription_count']}",
        f"- subscription latest total: {payload['summary']['subscription_latest_total']} {payload['currency']}",
        "",
        "## Subscriptions",
        "",
    ]
    for row in subscriptions["subscriptions"]:
        marker = " price increased" if row["price_increased"] else ""
        lines.append(
            f"- {row['label']}: {row['cadence']} {row['latest_amount']} {payload['currency']}{marker}"
        )
    lines += ["", "## Scenarios", ""]
    for row in payload["scenarios"]:
        lines.append(
            f"- {row['name']}: projected delta {row['projected_delta']} {payload['currency']}"
        )
    lines.append("")
    return "\n".join(lines)


def render_planning_summary(payload: dict[str, Any], subscriptions: dict[str, Any]) -> str:
    lines = [
        "# phantom-finance planning scenario proof",
        "",
        "Synthetic arithmetic only; not financial advice.",
        "",
        f"- month: {payload['month']}",
        f"- horizon: {payload['horizon_months']} months",
        f"- net worth: {payload['summary']['net_worth']} {payload['currency']}",
        f"- spendable cash: {payload['summary']['spendable_cash']} {payload['currency']}",
        f"- recurring subscription total: {payload['summary']['subscription_latest_total']} {payload['currency']}",
        f"- runway: {payload['runway']['runway_months']} months",
        f"- savings goal gap: {payload['savings_goal']['gap']} {payload['currency']}",
        "",
        "## Budget Snapshot",
        "",
    ]
    for row in payload["budgets"]:
        mark = "over plan" if row["over"] else "ok"
        lines.append(
            f"- {row['category']}: {row['spent']} / {row['limit']} {payload['currency']} ({mark})"
        )
    lines += ["", "## Recurring Signals", ""]
    for row in subscriptions["subscriptions"]:
        marker = " price increased" if row["price_increased"] else ""
        lines.append(
            f"- {row['label']}: {row['cadence']} {row['latest_amount']} {payload['currency']}{marker}"
        )
    lines += ["", "## Scenario Paths", ""]
    for row in payload["scenarios"]:
        months = row["months_to_goal"]
        months_text = "unreachable" if months is None else f"{months} months"
        lines.append(
            f"- {row['name']}: {row['projected_net_worth']} {payload['currency']} after horizon; goal in {months_text}"
        )
    lines.append("")
    return "\n".join(lines)


def write_scenario_demo_bundle(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    txns = synthetic_subscription_transactions()
    subs = subscriptions_artifact(txns)
    scenario_payload = subscription_scenario_artifact(txns)
    files = {
        "manifest.json": manifest(),
        "subscriptions.json": subs,
        "scenario.json": scenario_payload,
    }
    for name, payload in files.items():
        (out_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (out_dir / "summary.md").write_text(
        render_summary(scenario_payload, subs),
        encoding="utf-8",
    )
    return out_dir


def write_planning_scenario_bundle(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    txns = synthetic_subscription_transactions()
    subs = subscriptions_artifact(txns)
    scenario_payload = finance_planning_scenario_artifact(txns)
    files = {
        "manifest.json": planning_manifest(),
        "subscriptions.json": subs,
        "finance-scenario.json": scenario_payload,
    }
    for name, payload in files.items():
        (out_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (out_dir / "summary.md").write_text(
        render_planning_summary(scenario_payload, subs),
        encoding="utf-8",
    )
    return out_dir
