from decimal import Decimal

from phantom_finance import budget
from phantom_finance.ledger import Transaction


def txn(desc, amount, category, date="2026-06-05"):
    t = Transaction(date=date, amount=Decimal(amount), description=desc)
    t.category = category
    return t


def test_spend_by_category_expenses_only_transfers_excluded():
    txns = [
        txn("lunch", "-150", "dining"),
        txn("dinner", "-350", "dining"),
        txn("salary", "50000", "income"),
        txn("atm", "-3000", "transfer"),
        txn("last month", "-999", "dining", date="2026-05-31"),
    ]
    spent = budget.spend_by_category(txns, "2026-06")
    assert spent == {"dining": Decimal("500")}


def test_save_load_roundtrip():
    budget.save({"dining": Decimal("6000")})
    assert budget.load() == {"dining": Decimal("6000")}


def test_check_flags_over_plan():
    txns = [txn("feast", "-7000", "dining")]
    statuses = budget.check(txns, "2026-06", budgets={"dining": Decimal("6000")})
    assert len(statuses) == 1
    st = statuses[0]
    assert st.over
    assert st.spent == Decimal("7000")
    assert 1.1 < st.ratio < 1.2


def test_check_within_plan_and_unspent_category():
    statuses = budget.check([], "2026-06", budgets={"transport": Decimal("2000")})
    assert not statuses[0].over
    assert statuses[0].spent == Decimal("0")
