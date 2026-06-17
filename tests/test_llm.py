from __future__ import annotations

from decimal import Decimal

from phantom_finance import categorize, llm
from phantom_finance.ledger import Transaction


def test_make_categorizer_without_router_is_noop(monkeypatch):
    monkeypatch.delenv("PHANTOM_FINANCE_LLM", raising=False)

    categorizer = llm.make_categorizer()

    assert categorizer("anything unknown") is None


def test_make_categorizer_accepts_allowed_stub_category():
    categorizer = llm.make_categorizer(router=lambda prompt: "dining")

    assert categorizer("某不明小吃") == "dining"


def test_make_categorizer_rejects_hallucinated_category():
    categorizer = llm.make_categorizer(router=lambda prompt: "spaceships")

    assert categorizer("unknown merchant") is None


def test_make_categorizer_swallows_router_errors():
    def boom(prompt: str) -> str:
        raise RuntimeError("router unavailable")

    categorizer = llm.make_categorizer(router=boom)

    assert categorizer("unknown merchant") is None


def test_categorize_one_uses_llm_for_rule_miss():
    txn = Transaction(
        date="2026-06-17",
        amount=Decimal("-125"),
        description="No Match Merchant",
    )

    category = categorize.categorize_one(
        txn,
        llm=llm.make_categorizer(router=lambda prompt: "groceries"),
    )

    assert category == "groceries"


def test_categorize_one_rules_win_before_llm():
    def should_not_call(prompt: str) -> str:
        raise AssertionError("LLM should not be consulted for rule matches")

    txn = Transaction(
        date="2026-06-17",
        amount=Decimal("-125"),
        description="Starbucks Xinyi",
    )

    category = categorize.categorize_one(
        txn,
        llm=llm.make_categorizer(router=should_not_call),
    )

    assert category == "dining"


def test_default_router_returns_none_when_env_unset(monkeypatch):
    monkeypatch.delenv("PHANTOM_FINANCE_LLM", raising=False)

    assert llm.default_router() is None
