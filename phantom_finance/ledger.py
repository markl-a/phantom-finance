"""Append-only JSONL ledger.

Convention: signed amounts — negative = expense, positive = income
(matches most bank CSV exports). Amounts are Decimal end-to-end; floats
are rejected at the boundary so rounding errors can't creep in.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from contextlib import contextmanager
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
    """Parse '1,234.56' / '-120' / 'NT$300' / '(1,234)' style strings into Decimal.

    Accounting notation is honoured: a value wrapped in parentheses — e.g.
    ``(1,234)`` or ``NT$(500)`` — is a negative (debit), as many bank and
    credit-card CSV exports write expenses. A single trailing minus (``1234-``)
    is likewise treated as negative. Leading/trailing whitespace, thousands
    separators, and ``NT$`` / ``$`` / ``元`` symbols are stripped first.
    """
    cleaned = (
        raw.strip()
        .replace(",", "")
        .replace("NT$", "")
        .replace("$", "")
        .replace("元", "")
        .strip()
    )
    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        # accounting parentheses == negative (debit)
        cleaned = cleaned[1:-1].strip()
        negative = True
    elif cleaned.endswith("-"):
        # trailing-minus exports (e.g. "1234-")
        cleaned = cleaned[:-1].strip()
        negative = True
    try:
        value = Decimal(cleaned)
    except InvalidOperation as e:
        raise ValueError(f"cannot parse amount: {raw!r}") from e
    return -abs(value) if negative else value


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


@contextmanager
def _lock(path: Path, timeout: float = 10.0):
    lockfile = path.with_name(path.name + ".lock")
    start = time.monotonic()
    while True:
        try:
            fd = os.open(str(lockfile), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            if time.monotonic() - start > timeout:
                raise TimeoutError(f"ledger locked: {lockfile}")
            time.sleep(0.05)
        else:
            os.close(fd)
            break
    try:
        yield
    finally:
        try:
            lockfile.unlink()
        except FileNotFoundError:
            pass


def _atomic_write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line if line.endswith("\n") else line + "\n")
        f.flush()
        os.fsync(f.fileno())
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    os.replace(str(tmp), str(path))


def append(txns: list[Transaction], path: Path | None = None) -> list[Transaction]:
    """Append transactions, skipping txn_id duplicates. Returns what was written."""
    p = path or paths.ledger_path()
    with _lock(p):
        existing = load(p)
        seen = {t.txn_id for t in existing}
        fresh = [t for t in txns if t.txn_id not in seen]
        if fresh:
            _atomic_write(p, [t.to_json() for t in existing + fresh])
        return fresh


def rewrite(txns: list[Transaction], path: Path | None = None) -> None:
    """Rewrite the whole ledger (used after re-categorization)."""
    p = path or paths.ledger_path()
    with _lock(p):
        _atomic_write(p, [t.to_json() for t in txns])
