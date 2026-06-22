import json
from decimal import Decimal

from phantom_finance import categorize, paths
from phantom_finance.ledger import Transaction


def txn(desc: str, amount: str = "-100") -> Transaction:
    return Transaction(date="2026-06-01", amount=Decimal(amount), description=desc)


def test_derive_keyword_lowercases_and_trims():
    # a noisy bank description collapses to a stable, reusable keyword
    assert categorize.derive_keyword("  路邊滷味攤 #1234 ") == "路邊滷味攤 #1234"
    assert categorize.derive_keyword("STARBUCKS XINYI A1") == "starbucks xinyi a1"


def test_add_user_rule_creates_human_readable_json():
    categorize.add_user_rule("路邊滷味攤", "street-food")
    data = json.loads(paths.rules_path().read_text(encoding="utf-8"))
    assert data == {"路邊滷味攤": "street-food"}
    # round-trips through the existing loader
    assert categorize.load_user_rules()["路邊滷味攤"] == "street-food"


def test_add_user_rule_merges_without_clobbering_existing():
    paths.rules_path().write_text('{"全聯": "groceries"}', encoding="utf-8")
    categorize.add_user_rule("foodpanda", "delivery")
    data = json.loads(paths.rules_path().read_text(encoding="utf-8"))
    assert data == {"全聯": "groceries", "foodpanda": "delivery"}


def test_added_rule_is_used_by_categorizer():
    categorize.add_user_rule("某神秘商店", "shopping")
    assert categorize.categorize_one(txn("某神秘商店 信義店")) == "shopping"
