from __future__ import annotations

from decimal import Decimal

import pytest

from phantom_finance import ledger, recurring_store
from phantom_finance.cli import main
from phantom_finance.ledger import Transaction


def seed_netflix() -> None:
    ledger.append(
        [
            Transaction(date="2026-03-15", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-04-15", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-05-15", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-06-15", amount=Decimal("-420"), description="Netflix"),
        ]
    )


def test_recurring_list_empty(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["recurring"]) == 0
    assert "no recurring charges detected yet" in capsys.readouterr().out


def test_recurring_bare_syncs_and_lists_new(capsys: pytest.CaptureFixture[str]) -> None:
    seed_netflix()
    assert main(["recurring"]) == 0
    out = capsys.readouterr().out
    assert "[new" in out
    assert "Netflix" in out
    assert "PRICE UP" in out

    # bare `recurring` persisted the store
    records = recurring_store.load()
    assert records["netflix"].state == recurring_store.NEW


def test_recurring_review_then_filter_list(capsys: pytest.CaptureFixture[str]) -> None:
    seed_netflix()

    assert main(["recurring", "review", "Netflix"]) == 0
    assert "Netflix -> reviewed" in capsys.readouterr().out
    assert recurring_store.load()["netflix"].state == recurring_store.REVIEWED

    assert main(["recurring", "list", "--state", "reviewed"]) == 0
    assert "Netflix" in capsys.readouterr().out

    # ... and it is hidden when filtering for a different state
    assert main(["recurring", "list", "--state", "new"]) == 0
    out = capsys.readouterr().out
    assert "Netflix" not in out
    assert "no recurring charges in state 'new'" in out


def test_recurring_ignore_and_reset(capsys: pytest.CaptureFixture[str]) -> None:
    seed_netflix()

    assert main(["recurring", "ignore", "netflix"]) == 0
    assert recurring_store.load()["netflix"].state == recurring_store.IGNORED
    capsys.readouterr()

    assert main(["recurring", "reset", "netflix"]) == 0
    assert "Netflix -> new" in capsys.readouterr().out
    assert recurring_store.load()["netflix"].state == recurring_store.NEW


def test_recurring_review_unknown_merchant_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    seed_netflix()
    assert main(["recurring", "ignore", "spotify"]) == 1
    err = capsys.readouterr().err
    assert "error:" in err
    assert "spotify" in err
