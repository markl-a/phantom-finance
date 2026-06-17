from decimal import Decimal

import pytest

from phantom_finance import categorize, paths
from phantom_finance.ledger import Transaction


def txn(desc: str, amount: str = "-100") -> Transaction:
    return Transaction(date="2026-06-01", amount=Decimal(amount), description=desc)


def test_missing_rules_file_keeps_default_rules():
    assert categorize.categorize_one(txn("Starbucks Xinyi")) == "dining"


@pytest.mark.parametrize("content", ["", "   \n\t", "{}"])
def test_empty_rules_file_keeps_default_rules(content):
    paths.rules_path().write_text(content, encoding="utf-8")

    assert categorize.categorize_one(txn("Starbucks Xinyi")) == "dining"


def test_user_rule_overrides_default_rule():
    paths.rules_path().write_text('{"starbucks": "coffee-shops"}', encoding="utf-8")

    assert categorize.categorize_one(txn("Starbucks Xinyi")) == "coffee-shops"


def test_user_rule_for_unknown_merchant():
    paths.rules_path().write_text('{"某神秘商店": "shopping"}', encoding="utf-8")

    assert categorize.categorize_one(txn("某神秘商店")) == "shopping"


def test_apply_uses_user_rules():
    paths.rules_path().write_text('{"某神秘商店": "shopping"}', encoding="utf-8")
    t = txn("某神秘商店")

    assert categorize.apply([t]) == 1
    assert t.category == "shopping"


def test_malformed_rules_json_raises_value_error():
    paths.rules_path().write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid rules"):
        categorize.categorize_one(txn("Starbucks Xinyi"))


def test_rules_json_array_raises_value_error():
    paths.rules_path().write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a JSON object"):
        categorize.categorize_one(txn("Starbucks Xinyi"))


def test_user_rule_outranks_extra_rules():
    paths.rules_path().write_text('{"路邊攤": "street-food"}', encoding="utf-8")

    assert (
        categorize.categorize_one(txn("路邊攤滷味"), extra={"路邊攤": "dining"})
        == "street-food"
    )
