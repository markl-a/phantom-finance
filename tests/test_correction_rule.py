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


def test_learned_rule_matches_multi_space_description():
    # a multi-space description must yield a keyword that is a substring of itself
    categorize.add_user_rule(categorize.derive_keyword("路邊   滷味"), "street-food")
    assert categorize.categorize_one(txn("路邊   滷味 信義")) == "street-food"


from phantom_finance import cli, ledger


def test_recat_manual_correction_persists_rule_and_backfills():
    # two txns from the same merchant land uncategorized
    ledger.append([
        Transaction(date="2026-06-01", amount=Decimal("-250"), description="路邊滷味攤 信義"),
        Transaction(date="2026-06-09", amount=Decimal("-300"), description="路邊滷味攤 大安"),
    ])
    # operator corrects ONE: recat <match> <category>
    rc = cli.main(["recat", "路邊滷味攤", "street-food"])
    assert rc == 0
    # both existing txns are backfilled
    cats = {t.category for t in ledger.load()}
    assert cats == {"street-food"}
    # the correction became a durable rule
    assert categorize.load_user_rules()["路邊滷味攤"] == "street-food"


def test_recat_learned_rule_categorizes_future_import_offline():
    cli.main(["recat", "路邊滷味攤", "street-food"])
    # a NEW transaction from the same merchant, categorized with NO llm
    t = Transaction(date="2026-07-02", amount=Decimal("-180"), description="路邊滷味攤 內湖")
    assert categorize.categorize_one(t, llm=None) == "street-food"


def test_recat_no_args_still_reruns_uncategorized():
    ledger.append([Transaction(date="2026-06-01", amount=Decimal("-100"), description="全聯 週末")])
    rc = cli.main(["recat"])
    assert rc == 0
    assert ledger.load()[0].category == "groceries"
