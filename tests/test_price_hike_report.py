import json
from decimal import Decimal

from phantom_finance import ledger, paths
from phantom_finance.cli import main
from phantom_finance.ledger import Transaction


def _event_meta() -> dict:
    event_dirs = list(paths.events_dir().iterdir())
    assert len(event_dirs) == 1
    return json.loads((event_dirs[0] / "meta.json").read_text(encoding="utf-8"))


def test_price_hike_reaches_report_and_event():
    ledger.append(
        [
            Transaction(date="2026-03-05", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-04-05", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-05-05", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-06-05", amount=Decimal("-420"), description="Netflix"),
        ]
    )

    assert main(["report", "--month", "2026-06"]) == 0

    report = (paths.reports_dir() / "2026-06-report.md").read_text(encoding="utf-8")
    assert "## Subscription price changes" in report
    assert "Netflix" in report
    assert "monthly" in report
    assert "up 8%" in report

    meta = _event_meta()
    price_hikes = meta["payload"]["price_hikes"]
    assert price_hikes
    assert "netflix" in price_hikes[0]["merchant"].lower()
    assert price_hikes[0]["cadence"] == "monthly"
    assert price_hikes[0]["pct_change"] == 8


def test_no_hike_control_absent():
    ledger.append(
        [
            Transaction(date="2026-03-05", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-04-05", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-05-05", amount=Decimal("-390"), description="Netflix"),
            Transaction(date="2026-06-05", amount=Decimal("-390"), description="Netflix"),
        ]
    )

    assert main(["report", "--month", "2026-06"]) == 0

    report = (paths.reports_dir() / "2026-06-report.md").read_text(encoding="utf-8")
    assert "## Subscription price changes" not in report

    meta = _event_meta()
    assert meta["payload"]["price_hikes"] == []
