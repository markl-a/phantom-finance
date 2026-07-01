"""Tests for monthly report rendering of recurring charges."""

from __future__ import annotations

from decimal import Decimal

from phantom_finance import reporter
from phantom_finance.ledger import Transaction


def txn(date: str, amount: str, description: str, category: str = "expense") -> Transaction:
    t = Transaction(date=date, amount=Decimal(amount), description=description)
    t.category = category
    return t


def test_render_lists_recurring_charges():
    txns = [
        txn("2026-06-01", "-120", "Spotify"),
        txn("2026-06-15", "-120", "Spotify"),
        txn("2026-06-29", "-120", "Spotify"),
    ]

    text = reporter.render(txns, "2026-06")

    assert "## Recurring charges" in text
    assert "Spotify" in text
    assert "biweekly" in text
    assert "typical 120" in text

    for word in ["bad", "spent too much", "waste", "stop", "shame"]:
        assert word not in text.lower()
