from decimal import Decimal

from phantom_finance import taxcat
from phantom_finance.ledger import Transaction


def inc(desc: str, amount: str) -> Transaction:
    return Transaction(date="2026-06-01", amount=Decimal(amount), description=desc)


def test_freelance_income_classifies_9a():
    assert taxcat.classify(inc("某公司 程式設計 接案款", "30000")).income_type == "9A"
    assert taxcat.classify(inc("顧問費", "15000")).income_type == "9A"


def test_salary_classifies_salary():
    assert taxcat.classify(inc("六月份 薪資", "50000")).income_type == "salary"


def test_royalty_classifies_9b():
    assert taxcat.classify(inc("出版社 版稅", "8000")).income_type == "9B"


def test_dividend_interest_is_other_income():
    assert taxcat.classify(inc("台積電 股息", "5000")).income_type == "other_income"


def test_unknown_income_defaults_to_9a_for_freelancers():
    assert taxcat.classify(inc("某神秘入帳", "12000")).income_type == "9A"


def test_expense_has_no_income_type():
    assert taxcat.classify(inc("全聯", "-500")).income_type is None
