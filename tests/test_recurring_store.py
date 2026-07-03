from decimal import Decimal

import pytest

from phantom_finance import recurring, recurring_store
from phantom_finance.ledger import Transaction


def txn(date: str, amount: str, description: str) -> Transaction:
    return Transaction(date=date, amount=Decimal(amount), description=description)


NETFLIX_FLAT = [
    txn("2026-03-15", "-390", "Netflix"),
    txn("2026-04-15", "-390", "Netflix"),
    txn("2026-05-15", "-390", "Netflix"),
]

NETFLIX_HIKE = NETFLIX_FLAT + [txn("2026-06-15", "-420", "Netflix")]

GYM = [
    txn("2026-06-01", "-250", "Weekly Gym"),
    txn("2026-06-08", "-250", "Weekly Gym"),
    txn("2026-06-15", "-250", "Weekly Gym"),
    txn("2026-06-22", "-250", "Weekly Gym"),
]


# --- sync: recording detected charges -------------------------------------


def test_sync_records_new_charge_as_new():
    records = recurring_store.sync(recurring.detect(NETFLIX_FLAT), now="t1")

    assert set(records) == {"netflix"}
    rec = records["netflix"]
    assert rec.state == recurring_store.NEW
    assert rec.merchant == "Netflix"
    assert rec.cadence == "monthly"
    assert rec.occurrences == 3
    assert rec.typical_amount == Decimal("390")
    assert rec.first_seen == "t1"
    assert rec.last_updated == "t1"


def test_sync_is_persistent_and_survives_reload():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT))

    # fresh load from disk == a real round-trip through recurring.json
    reloaded = recurring_store.load()
    assert set(reloaded) == {"netflix"}
    rec = reloaded["netflix"]
    # Decimal typing preserved across serialization
    assert isinstance(rec.typical_amount, Decimal)
    assert rec.typical_amount == Decimal("390")
    assert isinstance(rec.latest_amount, Decimal)
    assert isinstance(rec.pct_change, float)
    assert rec.state == recurring_store.NEW


def test_store_round_trip_via_explicit_path(tmp_path):
    path = tmp_path / "recurring.json"
    recurring_store.sync(recurring.detect(NETFLIX_HIKE), path=path)

    assert path.exists()
    reloaded = recurring_store.load(path)
    rec = reloaded["netflix"]
    assert rec.occurrences == 4
    assert rec.latest_amount == Decimal("420")
    assert rec.price_increased is True
    assert round(rec.pct_change) == round(float(Decimal("30") / Decimal("390") * 100))


def test_load_missing_file_is_empty():
    assert recurring_store.load() == {}


def test_load_truncated_file_is_treated_as_empty(tmp_path):
    path = tmp_path / "recurring.json"
    path.write_text("   ", encoding="utf-8")
    assert recurring_store.load(path) == {}


def test_load_invalid_json_raises(tmp_path):
    path = tmp_path / "recurring.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        recurring_store.load(path)


# --- review state machine --------------------------------------------------


def test_walk_full_state_machine():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT))

    assert recurring_store.load()["netflix"].state == recurring_store.NEW

    rec = recurring_store.review("netflix")
    assert rec.state == recurring_store.REVIEWED
    assert recurring_store.load()["netflix"].state == recurring_store.REVIEWED

    rec = recurring_store.ignore("netflix")
    assert rec.state == recurring_store.IGNORED
    assert recurring_store.load()["netflix"].state == recurring_store.IGNORED

    rec = recurring_store.reset("netflix")
    assert rec.state == recurring_store.NEW
    assert recurring_store.load()["netflix"].state == recurring_store.NEW


def test_set_state_updates_timestamp_but_keeps_first_seen():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT), now="t1")
    rec = recurring_store.review("netflix", now="t2")
    assert rec.first_seen == "t1"
    assert rec.last_updated == "t2"


def test_same_state_is_idempotent_noop():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT), now="t1")
    # new -> new is a legal no-op and must not bump last_updated
    rec = recurring_store.set_state("netflix", recurring_store.NEW, now="t2")
    assert rec.state == recurring_store.NEW
    assert rec.last_updated == "t1"


def test_unknown_target_state_raises():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT))
    with pytest.raises(ValueError):
        recurring_store.set_state("netflix", "bogus")


def test_set_state_on_unknown_key_raises():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT))
    with pytest.raises(ValueError):
        recurring_store.set_state("does-not-exist", recurring_store.REVIEWED)


# --- sync preserves user decisions ----------------------------------------


def test_sync_preserves_review_decision_and_refreshes_detection():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT), now="t1")
    recurring_store.review("netflix", now="t2")

    # a later month arrives with a price hike; re-detect + sync
    updated = recurring_store.sync(recurring.detect(NETFLIX_HIKE), now="t3")
    rec = updated["netflix"]

    # decision survives ...
    assert rec.state == recurring_store.REVIEWED
    # ... but detection fields are refreshed
    assert rec.occurrences == 4
    assert rec.latest_amount == Decimal("420")
    assert rec.price_increased is True
    assert rec.first_seen == "t1"
    assert rec.last_updated == "t3"


def test_sync_adds_new_charges_without_disturbing_existing():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT))
    recurring_store.ignore("netflix")

    updated = recurring_store.sync(recurring.detect(NETFLIX_FLAT + GYM))

    assert updated["netflix"].state == recurring_store.IGNORED
    assert updated["weekly gym"].state == recurring_store.NEW


def test_ignored_charge_survives_dropping_out_of_detection():
    recurring_store.sync(recurring.detect(NETFLIX_FLAT))
    recurring_store.ignore("netflix")

    # a later sync with nothing detected must NOT drop or reset the record
    updated = recurring_store.sync([])
    assert updated["netflix"].state == recurring_store.IGNORED


# --- resolve_key -----------------------------------------------------------


def test_resolve_key_exact_and_substring():
    records = recurring_store.sync(recurring.detect(NETFLIX_FLAT + GYM))

    assert recurring_store.resolve_key("Netflix", records) == "netflix"
    assert recurring_store.resolve_key("netflix", records) == "netflix"
    assert recurring_store.resolve_key("gym", records) == "weekly gym"


def test_resolve_key_missing_and_ambiguous_raise():
    txns = [
        txn("2026-03-15", "-390", "Netflix"),
        txn("2026-04-15", "-390", "Netflix"),
        txn("2026-05-15", "-390", "Netflix"),
        txn("2026-03-10", "-99", "Netflix Games"),
        txn("2026-04-10", "-99", "Netflix Games"),
        txn("2026-05-10", "-99", "Netflix Games"),
    ]
    records = recurring_store.sync(recurring.detect(txns))

    with pytest.raises(ValueError):
        recurring_store.resolve_key("spotify", records)
    with pytest.raises(ValueError):
        # "netflix" is a substring of both "netflix" and "netflix games"...
        # but it is an EXACT key too, so that resolves; use a true ambiguity:
        recurring_store.resolve_key("net", records)
