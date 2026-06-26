from __future__ import annotations

import json
from pathlib import Path

from phantom_finance import paths
from phantom_finance.cli import main

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_monthly_summary_json_artifact_is_aggregate_only(capsys):
    out = paths.finance_home() / "artifacts" / "summary-2026-06.json"

    assert main(["account", "add", "cathay", "--type", "cash"]) == 0
    assert main(["import", str(FIXTURES / "bank_en.csv"), "--account", "cathay"]) == 0
    assert main(["recat", "Starbucks", "dining"]) == 0
    assert main(["budget", "set", "dining", "600"]) == 0

    capsys.readouterr()
    rc = main(["summary", "--month", "2026-06", "--json", "--out", str(out)])

    assert rc == 0
    printed = json.loads(capsys.readouterr().out)
    artifact = json.loads(out.read_text(encoding="utf-8"))
    assert printed == artifact
    assert artifact["schema_version"] == 1
    assert artifact["month"] == "2026-06"
    assert artifact["transaction_count"] == 3
    assert artifact["income"] == "50000"
    assert artifact["expense"] == "1350.50"
    assert artifact["net"] == "48649.50"
    assert artifact["net_worth"] == "48649.50"
    assert artifact["spendable_cash"] == "48649.50"
    assert artifact["by_category"] == [
        {"category": "groceries", "amount": "1200"},
        {"category": "dining", "amount": "150.50"},
    ]
    assert artifact["budgets"] == [
        {
            "category": "dining",
            "spent": "150.50",
            "limit": "600",
            "ratio": 0.2508,
            "over": False,
        }
    ]
    assert "transactions" not in artifact
    assert "Starbucks" not in out.read_text(encoding="utf-8")


def test_monthly_summary_text_output_is_human_readable(capsys):
    assert main(["import", str(FIXTURES / "bank_en.csv"), "--account", "cathay"]) == 0
    capsys.readouterr()

    rc = main(["summary", "--month", "2026-06"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "month: 2026-06" in out
    assert "transactions: 3" in out
    assert "net: 48649.50" in out
