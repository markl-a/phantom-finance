"""Keyword-rule categorizer with an optional LLM fallback hook.

Tier 1 is pure rules (works offline, deterministic, testable).
Tier 2 plugs an LLM callable in for whatever the rules miss — the hook
signature is already stable so phantom-mesh can wire its model router in
without touching this module.
"""

from __future__ import annotations

from typing import Callable, Optional

from .ledger import Transaction, UNCATEGORIZED

# keyword (lowercase substring) -> category; zh + en because real ledgers mix both
DEFAULT_RULES: dict[str, str] = {
    # groceries / convenience
    "全聯": "groceries", "家樂福": "groceries", "costco": "groceries",
    "supermarket": "groceries", "grocery": "groceries", "7-eleven": "groceries",
    "全家": "groceries", "便利商店": "groceries",
    # dining
    "restaurant": "dining", "cafe": "dining", "coffee": "dining",
    "starbucks": "dining", "mcdonald": "dining", "ubereats": "dining",
    "foodpanda": "dining", "餐": "dining", "早餐": "dining", "午餐": "dining",
    "晚餐": "dining", "飲料": "dining",
    # transport
    "uber": "transport", "taxi": "transport", "捷運": "transport",
    "高鐵": "transport", "台鐵": "transport", "悠遊": "transport",
    "easycard": "transport", "fuel": "transport", "加油": "transport",
    "停車": "transport",
    # utilities / telecom
    "電費": "utilities", "水費": "utilities", "瓦斯": "utilities",
    "中華電信": "utilities", "telecom": "utilities", "internet": "utilities",
    "電信": "utilities",
    # housing
    "房租": "housing", "rent": "housing", "mortgage": "housing", "管理費": "housing",
    # subscriptions
    "netflix": "subscription", "spotify": "subscription", "youtube": "subscription",
    "icloud": "subscription", "openai": "subscription", "anthropic": "subscription",
    "claude": "subscription", "github": "subscription", "訂閱": "subscription",
    # health
    "藥局": "health", "pharmacy": "health", "診所": "health", "clinic": "health",
    "hospital": "health", "醫院": "health", "健身": "health", "gym": "health",
    # entertainment
    "電影": "entertainment", "cinema": "entertainment", "steam": "entertainment",
    "game": "entertainment",
    # income
    "薪資": "income", "薪水": "income", "salary": "income", "payroll": "income",
    "股息": "income", "dividend": "income", "interest": "income", "利息": "income",
    # transfers (excluded from spend reports)
    "轉帳": "transfer", "transfer": "transfer", "atm": "transfer", "提款": "transfer",
}

# LLM hook: (description) -> category or None. Wired in Tier 2 via phantom-mesh router.
LlmCategorizer = Callable[[str], Optional[str]]


def categorize_one(
    txn: Transaction,
    rules: dict[str, str] | None = None,
    llm: LlmCategorizer | None = None,
) -> str:
    rules = DEFAULT_RULES if rules is None else rules
    desc = txn.description.lower()
    for keyword, category in rules.items():
        if keyword in desc:
            return category
    if llm is not None:
        guess = llm(txn.description)
        if guess:
            return guess
    # rules can't tell income from expense for unknown merchants; the sign can
    return "income" if txn.amount > 0 else UNCATEGORIZED


def apply(
    txns: list[Transaction],
    rules: dict[str, str] | None = None,
    llm: LlmCategorizer | None = None,
    only_uncategorized: bool = True,
) -> int:
    """Categorize in place. Returns how many transactions changed."""
    changed = 0
    for t in txns:
        if only_uncategorized and t.category != UNCATEGORIZED:
            continue
        new = categorize_one(t, rules=rules, llm=llm)
        if new != t.category:
            t.category = new
            changed += 1
    return changed
