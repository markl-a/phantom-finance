"""Append-only JSONL ledger.

Convention: signed amounts — negative = expense, positive = income
(matches most bank CSV exports). Amounts are Decimal end-to-end; floats
are rejected at the boundary so rounding errors can't creep in.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import paths

UNCATEGORIZED = "uncategorized"


@dataclass
class Transaction:
    date: str  # ISO YYYY-MM-DD
    amount: Decimal  # signed: negative = expense, positive = income
    description: str
    account: str = "default"
    category: str = UNCATEGORIZED
    currency: str = "TWD"
    txn_id: str = field(default="")

    def __post_init__(self) -> None:
        if isinstance(self.amount, float):
            raise TypeError("amount must be Decimal or str, never float")
        self.amount = Decimal(str(self.amount))
        if not self.txn_id:
            raw = f"{self.date}|{self.amount}|{self.description}|{self.account}"
            self.txn_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    @property
    def month(self) -> str:
        return self.date[:7]

    def to_json(self) -> str:
        d = asdict(self)
        d["amount"] = str(self.amount)
        return json.dumps(d, ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "Transaction":
        d = json.loads(line)
        d["amount"] = Decimal(d["amount"])
        return cls(**d)


def parse_amount(raw: str) -> Decimal:
    """Parse '1,234.56' / '-120' / 'NT$300' style strings into Decimal."""
    cleaned = (
        raw.strip()
        .replace(",", "")
        .replace("NT$", "")
        .replace("$", "")
        .replace("元", "")
    )
    try:
        return Decimal(cleaned)
    except InvalidOperation as e:
        raise ValueError(f"cannot parse amount: {raw!r}") from e


def load(path: Path | None = None) -> list[Transaction]:
    p = path or paths.ledger_path()
    if not p.exists():
        return []
    txns = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            txns.append(Transaction.from_json(line))
    return txns


def append(txns: list[Transaction], path: Path | None = None) -> list[Transaction]:
    """Append transactions, skipping txn_id duplicates. Returns what was written."""
    p = path or paths.ledger_path()
    seen = {t.txn_id for t in load(p)}
    fresh = [t for t in txns if t.txn_id not in seen]
    if fresh:
        with p.open("a", encoding="utf-8") as f:
            for t in fresh:
                f.write(t.to_json() + "\n")
    return fresh


def rewrite(txns: list[Transaction], path: Path | None = None) -> None:
    """Rewrite the whole ledger (used after re-categorization)."""
    p = path or paths.ledger_path()
    tmp = p.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for t in txns:
            f.write(t.to_json() + "\n")
    tmp.replace(p)
