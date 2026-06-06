from decimal import Decimal

import pytest

from phantom_finance import ledger
from phantom_finance.ledger import Transaction, parse_amount


def test_append_and_load_roundtrip():
    t = Transaction(date="2026-06-01", amount=Decimal("-120"), description="全聯 groceries")
    written = ledger.append([t])
    assert len(written) == 1
    loaded = ledger.load()
    assert len(loaded) == 1
    assert loaded[0].amount == Decimal("-120")
    assert loaded[0].description == "全聯 groceries"
    assert loaded[0].txn_id == t.txn_id


def test_append_dedupes_by_txn_id():
    t = Transaction(date="2026-06-01", amount=Decimal("-120"), description="dup")
    assert len(ledger.append([t])) == 1
    again = Transaction(date="2026-06-01", amount=Decimal("-120"), description="dup")
    assert len(ledger.append([again])) == 0
    assert len(ledger.load()) == 1


def test_float_amount_rejected():
    with pytest.raises(TypeError):
        Transaction(date="2026-06-01", amount=12.5, description="float sneaks in")


def test_parse_amount_formats():
    assert parse_amount("1,234.56") == Decimal("1234.56")
    assert parse_amount("-120") == Decimal("-120")
    assert parse_amount("NT$300") == Decimal("300")
    assert parse_amount("500元") == Decimal("500")
    with pytest.raises(ValueError):
        parse_amount("not money")


def test_rewrite_replaces_ledger():
    t1 = Transaction(date="2026-06-01", amount=Decimal("-1"), description="a")
    t2 = Transaction(date="2026-06-02", amount=Decimal("-2"), description="b")
    ledger.append([t1, t2])
    t1.category = "dining"
    ledger.rewrite([t1, t2])
    loaded = ledger.load()
    assert len(loaded) == 2
    assert loaded[0].category == "dining"
