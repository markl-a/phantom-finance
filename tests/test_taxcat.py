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


def test_business_category_expense_is_deductible_candidate():
    t = inc("中華電信 網路費", "-899")
    t.category = "utilities"
    assert taxcat.classify(t).deductible_candidate is True


def test_personal_category_expense_is_not_deductible():
    t = inc("星巴克", "-160")
    t.category = "dining"
    assert taxcat.classify(t).deductible_candidate is False


def test_large_single_income_flags_nhi_supplement():
    # single payment >= NT$20,000 triggers 二代健保補充保費 (2.11%)
    assert taxcat.classify(inc("接案款", "20000")).nhi_supplement_flag is True
    assert taxcat.classify(inc("接案款", "19999")).nhi_supplement_flag is False


def test_9a_income_flags_withholding():
    assert taxcat.classify(inc("顧問費", "30000")).withholding_flag is True
    # salary / other income are not 9A withholding
    assert taxcat.classify(inc("薪資", "50000")).withholding_flag is False


def test_positive_transfer_is_not_taxable_income():
    # a positive transfer (incoming transfer / refund / ATM deposit) is NOT income
    t = inc("ATM 存款", "25000")
    t.category = "transfer"
    info = taxcat.classify(t)
    assert info.income_type is None
    assert info.nhi_supplement_flag is False
    assert info.withholding_flag is False
