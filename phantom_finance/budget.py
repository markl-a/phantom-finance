"""Monthly budgets per category, stored as plain JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from . import paths
from .ledger import Transaction


@dataclass
class BudgetStatus:
    category: str
    spent: Decimal
    limit: Decimal

    @property
    def ratio(self) -> float:
        return float(self.spent / self.limit) if self.limit else 0.0

    @property
    def over(self) -> bool:
        return self.spent > self.limit


def load(path: Path | None = None) -> dict[str, Decimal]:
    p = path or paths.budgets_path()
    if not p.exists():
        return {}

    raw_text = p.read_text(encoding="utf-8")
    if not raw_text.strip():
        # a truncated / half-written file is treated as "no budgets", not a crash
        return {}

    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid budgets file {p}: {e.msg}") from e

    if not isinstance(raw, dict):
        raise ValueError(f"budgets file {p} must be a JSON object of category -> limit")

    return {k: Decimal(str(v)) for k, v in raw.items()}


def save(budgets: dict[str, Decimal], path: Path | None = None) -> None:
    p = path or paths.budgets_path()
    p.write_text(
        json.dumps({k: str(v) for k, v in budgets.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def spend_by_category(txns: list[Transaction], month: str) -> dict[str, Decimal]:
    """Sum of expenses (abs) per category for a YYYY-MM month. Transfers excluded."""
    out: dict[str, Decimal] = {}
    for t in txns:
        if t.month != month or t.amount >= 0 or t.category == "transfer":
            continue
        out[t.category] = out.get(t.category, Decimal(0)) + (-t.amount)
    return out


def check(
    txns: list[Transaction], month: str, budgets: dict[str, Decimal] | None = None
) -> list[BudgetStatus]:
    budgets = load() if budgets is None else budgets
    spent = spend_by_category(txns, month)
    return [
        BudgetStatus(category=cat, spent=spent.get(cat, Decimal(0)), limit=limit)
        for cat, limit in sorted(budgets.items())
    ]
