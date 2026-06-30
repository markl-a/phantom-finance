import pytest

pytest.importorskip("mcp")

from decimal import Decimal

from phantom_finance import ledger
from phantom_finance.ledger import Transaction
from phantom_finance.mcp_server import finance_monthly_summary


def test_finance_monthly_summary_returns_artifact_from_isolated_ledger():
    txn = Transaction(
        date="2026-06-05",
        amount=Decimal("-120"),
        description="synthetic lunch",
        category="dining",
    )
    ledger.append([txn])

    result = finance_monthly_summary(month="2026-06")

    assert isinstance(result, dict)
    assert {
        "schema_version",
        "month",
        "currency",
        "transaction_count",
        "income",
        "expense",
        "net",
        "net_worth",
        "spendable_cash",
        "by_category",
        "budgets",
    }.issubset(result)
    assert result["month"] == "2026-06"
    assert result["currency"] == "TWD"
    assert result["transaction_count"] == 1
    assert result["income"] == "0"
    assert result["expense"] == "120"
    assert result["net"] == "-120"
    assert result["by_category"] == [{"category": "dining", "amount": "120"}]
