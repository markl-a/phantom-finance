import json
from decimal import Decimal

from phantom_finance import ledger, networth, paths, reporter
from phantom_finance.ledger import Transaction


def txn(desc, amount, category, date="2026-06-05"):
    t = Transaction(date=date, amount=Decimal(amount), description=desc)
    t.category = category
    return t


SAMPLE = [
    txn("salary", "50000", "income", date="2026-06-01"),
    txn("rent", "-18000", "housing"),
    txn("feast", "-7000", "dining"),
    txn("atm", "-3000", "transfer"),
]


def test_month_summary_excludes_transfers():
    s = reporter.month_summary(SAMPLE, "2026-06")
    assert s["income"] == Decimal("50000")
    assert s["expense"] == Decimal("25000")  # transfer not counted
    assert s["net"] == Decimal("25000")
    assert s["txn_count"] == 3


def test_render_is_shame_free():
    text = reporter.render(SAMPLE, "2026-06")
    assert "# phantom-finance · 2026-06" in text
    assert "housing: 18000" in text
    for shaming in ["overspent", "again", "fail", "bad", "should have"]:
        assert shaming not in text.lower()


def test_render_shows_net_worth_and_spendable_cash():
    text = reporter.render(SAMPLE, "2026-06")
    assert f"- net worth: {networth.net_worth(SAMPLE)}" in text
    assert f"- spendable cash: {networth.cashflow_total(SAMPLE)}" in text


def test_write_report_creates_file_and_event():
    ledger.append(SAMPLE)
    out = reporter.write_report("2026-06")
    assert out.exists()
    assert out.name == "2026-06-report.md"
    # one event emitted with the right payload
    event_dirs = list(paths.events_dir().iterdir())
    assert len(event_dirs) == 1
    meta = json.loads((event_dirs[0] / "meta.json").read_text(encoding="utf-8"))
    assert meta["source"] == "phantom-finance"
    assert meta["kind"] == "monthly-report"
    assert meta["payload"]["net"] == "25000"
