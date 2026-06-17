from decimal import Decimal

import pytest

from phantom_finance import ledger
from phantom_finance.ledger import Transaction


def txn(description: str, amount: str = "-100") -> Transaction:
    return Transaction(
        date="2026-06-01",
        amount=Decimal(amount),
        description=description,
    )


def test_append_then_rewrite_round_trips(tmp_path):
    path = tmp_path / "ledger.jsonl"
    a = txn("a")
    b = txn("b", "-200")

    assert ledger.append([a], path=path) == [a]
    b.category = "utilities"
    ledger.rewrite([a, b], path=path)

    loaded = ledger.load(path)
    assert loaded == [a, b]
    assert loaded[1].category == "utilities"


def test_second_write_creates_backup_with_prior_state(tmp_path):
    path = tmp_path / "ledger.jsonl"
    a = txn("a")
    b = txn("b", "-200")

    ledger.append([a], path=path)
    ledger.append([b], path=path)

    backup = path.with_name(path.name + ".bak")
    assert backup.exists()
    assert ledger.load(backup) == [a]
    assert ledger.load(path) == [a, b]


def test_idempotent_reimport_writes_transaction_once(tmp_path):
    path = tmp_path / "ledger.jsonl"
    a = txn("x")

    assert ledger.append([a], path=path) == [a]
    assert ledger.append([a], path=path) == []

    assert ledger.load(path) == [a]


def test_lock_times_out_when_already_held(tmp_path):
    path = tmp_path / "ledger.jsonl"

    with ledger._lock(path):
        with pytest.raises(TimeoutError):
            with ledger._lock(path, timeout=0.2):
                pass
