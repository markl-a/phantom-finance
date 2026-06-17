from decimal import Decimal

from phantom_finance import recurring
from phantom_finance.ledger import Transaction


def txn(date: str, amount: str, description: str) -> Transaction:
    return Transaction(date=date, amount=Decimal(amount), description=description)


def test_detects_monthly_subscription_with_price_hike():
    txns = [
        txn("2026-03-15", "-390", "Netflix"),
        txn("2026-04-15", "-390", "Netflix"),
        txn("2026-05-15", "-390", "Netflix"),
        txn("2026-06-15", "-420", "Netflix"),
    ]

    charges = recurring.detect(txns)

    assert len(charges) == 1
    charge = charges[0]
    assert charge.cadence == "monthly"
    assert charge.occurrences == 4
    assert charge.price_increased is True
    assert charge.pct_change == float(Decimal("30") / Decimal("390") * Decimal("100"))
    assert charge.latest_amount == Decimal("420")


def test_one_off_purchase_is_not_recurring():
    txns = [txn("2026-06-01", "-1200", "One Off Store")]

    assert recurring.detect(txns) == []


def test_irregular_merchant_is_excluded():
    txns = [
        txn("2026-01-01", "-100", "Random Merchant"),
        txn("2026-01-03", "-100", "Random Merchant"),
        txn("2026-02-19", "-100", "Random Merchant"),
    ]

    assert recurring.detect(txns) == []


def test_detects_weekly_flat_subscription():
    txns = [
        txn("2026-06-01", "-250", "Weekly Gym"),
        txn("2026-06-08", "-250", "Weekly Gym"),
        txn("2026-06-15", "-250", "Weekly Gym"),
        txn("2026-06-22", "-250", "Weekly Gym"),
    ]

    charges = recurring.detect(txns)

    assert len(charges) == 1
    charge = charges[0]
    assert charge.cadence == "weekly"
    assert charge.price_increased is False
    assert charge.pct_change == 0.0


def test_price_hikes_returns_only_increased_subscription():
    txns = [
        txn("2026-03-15", "-390", "Netflix"),
        txn("2026-04-15", "-390", "Netflix"),
        txn("2026-05-15", "-390", "Netflix"),
        txn("2026-06-15", "-420", "Netflix"),
        txn("2026-06-01", "-250", "Weekly Gym"),
        txn("2026-06-08", "-250", "Weekly Gym"),
        txn("2026-06-15", "-250", "Weekly Gym"),
        txn("2026-06-22", "-250", "Weekly Gym"),
        txn("2026-01-01", "-100", "Random Merchant"),
        txn("2026-01-03", "-100", "Random Merchant"),
        txn("2026-02-19", "-100", "Random Merchant"),
    ]

    hikes = recurring.price_hikes(txns)

    assert len(hikes) == 1
    assert hikes[0].merchant == "Netflix"
