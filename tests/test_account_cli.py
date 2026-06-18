from __future__ import annotations

from decimal import Decimal

import pytest

from phantom_finance import networth
from phantom_finance.cli import main
from phantom_finance.ledger import Transaction


def test_account_cli_written_accounts_drive_cashflow_vs_net_worth(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["account", "add", "brokerage", "--type", "asset"]) == 0
    assert main(["account", "add", "wallet", "--type", "cash"]) == 0

    capsys.readouterr()
    assert main(["account", "list"]) == 0
    out = capsys.readouterr().out

    assert "brokerage  asset  TWD" in out
    assert "wallet  cash  TWD" in out

    txns = [
        Transaction(
            date="2026-06-01",
            amount=Decimal("-500"),
            description="wallet spend",
            account="wallet",
        ),
        Transaction(
            date="2026-06-01",
            amount=Decimal("-20000"),
            description="brokerage buy",
            account="brokerage",
        ),
    ]

    assert networth.cashflow_total(txns) == Decimal("-500")
    assert networth.net_worth(txns) == Decimal("-20500")


def test_account_cli_set_type_round_trips_through_account_types() -> None:
    assert main(["account", "add", "x", "--type", "cash"]) == 0
    assert main(["account", "set-type", "x", "asset"]) == 0

    assert networth.load_account_types()["x"] == "asset"
