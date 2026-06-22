"""Deterministic Taiwan tax classification for freelancers / 一人公司.

PHASE-1 SCOPE + SAFETY: this is "報稅前整理" (filing prep), NOT tax advice. Every
mapping is a rule in a swappable config dict (so other jurisdictions can be added
later without touching the engine), and the LLM is never involved in tax/amount
logic. Outputs are clearly "候選 / 待確認" — the operator or their 記帳士 decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .ledger import Transaction

# description keyword (lowercase substring) -> Taiwan income type
INCOME_TYPE_RULES: dict[str, str] = {
    "薪資": "salary", "薪水": "salary", "salary": "salary", "payroll": "salary",
    "稿費": "9A", "演講": "9A", "授課": "9A", "鐘點": "9A", "設計": "9A",
    "程式": "9A", "開發": "9A", "顧問": "9A", "接案": "9A", "外包": "9A",
    "freelance": "9A", "consult": "9A", "translation": "9A", "翻譯": "9A",
    "版稅": "9B", "權利金": "9B", "royalty": "9B",
    "股息": "other_income", "股利": "other_income", "dividend": "other_income",
    "利息": "other_income", "interest": "other_income",
}
# 接案族 default: unknown professional income is a 9A candidate (most common case)
DEFAULT_INCOME_TYPE = "9A"

# expense categories (from categorize.py) that MIGHT be business-deductible.
# "candidate" only — the operator / 記帳士 confirms; never auto-claimed.
DEDUCTIBLE_CANDIDATE_CATEGORIES: set[str] = {
    "utilities", "transport", "subscription", "equipment", "software", "office",
}
# single income payment at/above this triggers 二代健保補充保費 (2.11%)
NHI_SUPPLEMENT_THRESHOLD = Decimal("20000")


@dataclass(frozen=True)
class TaxInfo:
    income_type: str | None  # "9A"|"9B"|"salary"|"other_income" for income; None for expenses
    deductible_candidate: bool
    nhi_supplement_flag: bool
    withholding_flag: bool


def _income_type(description: str) -> str:
    desc = description.lower()
    for keyword, itype in INCOME_TYPE_RULES.items():
        if keyword in desc:
            return itype
    return DEFAULT_INCOME_TYPE


def classify(txn: Transaction) -> TaxInfo:
    if txn.amount > 0:
        itype = _income_type(txn.description)
        return TaxInfo(
            income_type=itype,
            deductible_candidate=False,
            nhi_supplement_flag=txn.amount >= NHI_SUPPLEMENT_THRESHOLD,
            withholding_flag=itype == "9A",
        )
    return TaxInfo(
        income_type=None,
        deductible_candidate=txn.category in DEDUCTIBLE_CANDIDATE_CATEGORIES,
        nhi_supplement_flag=False,
        withholding_flag=False,
    )
