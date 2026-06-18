from __future__ import annotations

from decimal import Decimal

import pytest

from phantom_finance import ledger, networth
from phantom_finance.cli import main
from phantom_finance.ledger import Transaction


def test_net_worth_cli_prints_net_worth_and_spendable_cash(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["account", "add", "brokerage", "--type", "asset"]) == 0
    assert main(["account", "add", "wallet", "--type", "cash"]) == 0

    ledger.append(
        [
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
    )

    txns = ledger.load()
    expected_net_worth = networth.net_worth(txns)
    expected_spendable_cash = networth.cashflow_total(txns)

    capsys.readouterr()
    assert main(["net-worth"]) == 0
    out = capsys.readouterr().out

    assert f"net worth: {expected_net_worth} TWD" in out
    assert f"spendable cash: {expected_spendable_cash} TWD" in out


def test_net_worth_cli_accepts_currency_argument() -> None:
    assert main(["net-worth", "--currency", "TWD"]) == 0
