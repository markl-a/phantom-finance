from decimal import Decimal

from phantom_finance import ledger, recurring
from phantom_finance.cli import main
from phantom_finance.ledger import Transaction


def _txn(d, a, desc):
    return Transaction(date=d, amount=Decimal(a), description=desc)


def test_recurring_persists_review_state_and_resurfaces_on_price_hike(capsys):
    ledger.append(
        [
            _txn("2026-03-15", "-390", "Netflix"),
            _txn("2026-04-15", "-390", "Netflix"),
            _txn("2026-05-15", "-390", "Netflix"),
        ]
    )
    assert main(["recurring"]) == 0
    store = recurring.load_store()
    assert len(store) == 1
    key = next(iter(store))
    assert store[key]["status"] == "new"
    assert main(["recurring", "review", key, "--status", "ignored"]) == 0
    assert recurring.load_store()[key]["status"] == "ignored"
    assert main(["recurring"]) == 0
    assert recurring.load_store()[key]["status"] == "ignored"
    ledger.append([_txn("2026-06-15", "-420", "Netflix")])
    assert main(["recurring"]) == 0
    reload = recurring.load_store()[key]
    assert reload["status"] == "new"
    assert round(reload["price_hike_pct"]) > 0
    capsys.readouterr()
    assert main(["recurring", "list", "--status", "new"]) == 0
    out = capsys.readouterr().out
    assert key in out and "PRICE UP" in out
