from decimal import Decimal

import pytest

from phantom_finance import paths
from phantom_finance.ledger import Transaction
from phantom_finance.networth import (
    cashflow_total,
    convert,
    load_rates,
    net_worth,
)


def txn(amount: str, currency: str = "TWD", account: str = "cash") -> Transaction:
    return Transaction(
        date="2026-06-01",
        amount=Decimal(amount),
        description="test",
        currency=currency,
        account=account,
    )


def test_convert_twd_identity_returns_amount_unchanged():
    amount = Decimal("123.45")
    assert convert(amount, "TWD", "TWD") == amount


def test_convert_usd_to_twd_with_loaded_rates():
    paths.rates_path().write_text('{"USD": "31.5"}', encoding="utf-8")

    assert convert(Decimal("10"), "USD", "TWD") == Decimal("315")


def test_convert_unknown_currency_raises_value_error():
    with pytest.raises(ValueError, match="unknown currency 'USD'"):
        convert(Decimal("10"), "USD", "TWD", rates={"TWD": Decimal("1")})


def test_load_rates_missing_file_returns_default():
    assert load_rates() == {"TWD": Decimal("1")}


def test_load_rates_malformed_json_raises_value_error():
    paths.rates_path().write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid rates file"):
        load_rates()


def test_load_rates_json_array_raises_value_error():
    paths.rates_path().write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a JSON object"):
        load_rates()


def test_net_worth_converts_multiple_currencies():
    rates = {"TWD": Decimal("1"), "USD": Decimal("31.5")}

    assert net_worth([txn("1000"), txn("10", currency="USD")], rates=rates) == Decimal("1315")


def test_cashflow_total_excludes_asset_accounts_but_net_worth_includes_them():
    paths.accounts_path().write_text('{"brokerage": "asset"}', encoding="utf-8")
    txns = [txn("-500", account="cash"), txn("-20000", account="brokerage")]

    assert cashflow_total(txns) == Decimal("-500")
    assert net_worth(txns) == Decimal("-20500")


def test_backward_compat_without_rates_or_accounts_uses_plain_twd_sum():
    txns = [txn("1000"), txn("-250")]

    assert net_worth(txns) == Decimal("750")
    assert cashflow_total(txns) == Decimal("750")
