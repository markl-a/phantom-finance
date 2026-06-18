from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from . import paths
from .ledger import Transaction

BASE = "TWD"
ACCOUNT_TYPES = {"cash", "asset"}


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


def _read_accounts(path: Path | None = None) -> dict[str, object]:
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

    return data


def _validate_account_type(account: str, account_type: str) -> None:
    if account_type not in ACCOUNT_TYPES:
        raise ValueError(
            f"account type must be cash or asset for {account!r}: {account_type!r}"
        )


def load_account_types(path: Path | None = None) -> dict[str, str]:
    accounts = load_accounts(path)
    return {account: data["type"] for account, data in accounts.items()}


def load_accounts(path: Path | None = None) -> dict[str, dict[str, str]]:
    data = _read_accounts(path)

    accounts = {}
    for raw_account, raw_account_data in data.items():
        account = str(raw_account)
        if isinstance(raw_account_data, dict):
            account_type = str(raw_account_data.get("type")).lower()
            currency = str(raw_account_data.get("currency", BASE))
        else:
            account_type = str(raw_account_data).lower()
            currency = BASE

        _validate_account_type(account, account_type)
        accounts[account] = {"type": account_type, "currency": currency}

    return accounts


def save_account(
    name: str,
    account_type: str,
    currency: str = BASE,
    path: Path | None = None,
) -> None:
    account_type = account_type.lower()
    _validate_account_type(name, account_type)

    p = path or paths.accounts_path()
    accounts = load_accounts(p)
    accounts[name] = {"type": account_type, "currency": currency}

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(accounts, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def set_account_type(name: str, account_type: str, path: Path | None = None) -> None:
    p = path or paths.accounts_path()
    accounts = load_accounts(p)
    if name not in accounts:
        raise ValueError(f"account does not exist: {name}")

    save_account(name, account_type, accounts[name]["currency"], p)


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
