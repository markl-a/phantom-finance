from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from . import paths
from .ledger import Transaction

BASE = "TWD"


def load_rates(path: Path | None = None) -> dict[str, Decimal]:
    p = path or paths.rates_path()
    if not p.exists():
        return {BASE: Decimal("1")}

    raw = p.read_text(encoding="utf-8")
    if not raw.strip():
        return {BASE: Decimal("1")}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid rates file {p}: {e.msg}") from e

    if not isinstance(data, dict):
        raise ValueError(f"rates file {p} must be a JSON object")

    rates = {str(ccy): Decimal(str(rate)) for ccy, rate in data.items()}
    rates.setdefault(BASE, Decimal("1"))
    return rates


def convert(
    amount: Decimal,
    from_ccy: str,
    to_ccy: str = BASE,
    rates: dict[str, Decimal] | None = None,
) -> Decimal:
    rates = load_rates() if rates is None else rates
    if from_ccy == to_ccy:
        return amount

    for ccy in (from_ccy, to_ccy):
        if ccy not in rates:
            known = ", ".join(sorted(rates))
            raise ValueError(f"unknown currency {ccy!r}; known: {known}")

    return amount * rates[from_ccy] / rates[to_ccy]


def load_account_types(path: Path | None = None) -> dict[str, str]:
    p = path or paths.accounts_path()
    if not p.exists():
        return {}

    raw = p.read_text(encoding="utf-8")
    if not raw.strip():
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid accounts file {p}: {e.msg}") from e

    if not isinstance(data, dict):
        raise ValueError(f"accounts file {p} must be a JSON object")

    account_types = {str(account): str(account_type).lower() for account, account_type in data.items()}
    for account, account_type in account_types.items():
        if account_type not in {"cash", "asset"}:
            raise ValueError(
                f"account type must be cash or asset for {account!r}: {account_type!r}"
            )
    return account_types


def net_worth(
    txns: Iterable[Transaction],
    base: str = BASE,
    rates: dict[str, Decimal] | None = None,
) -> Decimal:
    rates = load_rates() if rates is None else rates
    total = Decimal("0")
    for txn in txns:
        total += convert(txn.amount, txn.currency, base, rates)
    return total


def cashflow_total(
    txns: Iterable[Transaction],
    base: str = BASE,
    rates: dict[str, Decimal] | None = None,
    account_types: dict[str, str] | None = None,
) -> Decimal:
    rates = load_rates() if rates is None else rates
    account_types = load_account_types() if account_types is None else account_types

    total = Decimal("0")
    for txn in txns:
        if account_types.get(txn.account, "cash") != "asset":
            total += convert(txn.amount, txn.currency, base, rates)
    return total
