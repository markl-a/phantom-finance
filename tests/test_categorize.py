from decimal import Decimal

from phantom_finance import categorize
from phantom_finance.ledger import Transaction, UNCATEGORIZED


def txn(desc, amount="-100"):
    return Transaction(date="2026-06-01", amount=Decimal(amount), description=desc)


def test_zh_and_en_rules():
    assert categorize.categorize_one(txn("全聯福利中心")) == "groceries"
    assert categorize.categorize_one(txn("Starbucks Xinyi")) == "dining"
    assert categorize.categorize_one(txn("台北捷運加值")) == "transport"
    assert categorize.categorize_one(txn("Netflix subscription")) == "subscription"
    assert categorize.categorize_one(txn("六月薪資", amount="50000")) == "income"


def test_unknown_expense_stays_uncategorized():
    assert categorize.categorize_one(txn("某個神秘商店")) == UNCATEGORIZED


def test_unknown_income_categorized_by_sign():
    assert categorize.categorize_one(txn("mystery deposit", amount="999")) == "income"


def test_llm_hook_used_as_fallback_only():
    calls = []

    def fake_llm(desc):
        calls.append(desc)
        return "entertainment"

    # rule hit -> LLM not called
    assert categorize.categorize_one(txn("starbucks"), llm=fake_llm) == "dining"
    assert calls == []
    # rule miss -> LLM called
    assert categorize.categorize_one(txn("神秘商店"), llm=fake_llm) == "entertainment"
    assert calls == ["神秘商店"]


def test_apply_only_touches_uncategorized():
    a = txn("starbucks")
    b = txn("神秘商店")
    b.category = "health"  # user set manually — must be preserved
    changed = categorize.apply([a, b])
    assert changed == 1
    assert a.category == "dining"
    assert b.category == "health"
