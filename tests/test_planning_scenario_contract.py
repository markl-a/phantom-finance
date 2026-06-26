from __future__ import annotations

import json

from phantom_finance import scenario
from phantom_finance.cli import main


def test_planning_scenario_bundle_proves_recurring_networth_usefulness(tmp_path):
    out = tmp_path / "planning-scenario"

    result = scenario.write_planning_scenario_bundle(out)

    assert result == out
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    subscriptions = json.loads((out / "subscriptions.json").read_text(encoding="utf-8"))
    scenario_payload = json.loads((out / "finance-scenario.json").read_text(encoding="utf-8"))
    summary = (out / "summary.md").read_text(encoding="utf-8")

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_finance_planning_scenario"
    assert manifest["synthetic_only"] is True
    assert manifest["live_account_aggregation"] is False
    assert manifest["bank_credentials_required"] is False
    assert manifest["financial_advice"] is False
    assert manifest["external_network"] is False
    assert manifest["cloud_llm"] is False
    assert manifest["artifacts"] == [
        "manifest.json",
        "subscriptions.json",
        "finance-scenario.json",
        "summary.md",
    ]

    assert subscriptions["subscriptions"]
    assert scenario_payload["schema_version"] == 1
    assert scenario_payload["mode"] == "synthetic_finance_planning_scenario"
    assert scenario_payload["data_policy"] == "synthetic_only"
    assert scenario_payload["financial_advice"] is False
    assert scenario_payload["live_account_aggregation"] is False
    assert scenario_payload["raw_transaction_rows_included"] is False
    assert scenario_payload["summary"]["month"] == "2026-06"
    assert scenario_payload["summary"]["monthly_net"] == "42030"
    assert scenario_payload["summary"]["net_worth"] == "186210"
    assert scenario_payload["summary"]["spendable_cash"] == "186210"
    assert scenario_payload["summary"]["subscription_latest_total"] == "1970"

    runway = scenario_payload["runway"]
    assert runway["monthly_expense"] == "7970"
    assert runway["runway_months"] == 23.36
    assert runway["subscription_share_of_expense_pct"] == 24.72

    assert scenario_payload["savings_goal"]["target_amount"] == "400000"
    assert scenario_payload["savings_goal"]["gap"] == "213790"
    assert scenario_payload["savings_goal"]["baseline_months_to_goal"] == 6
    assert scenario_payload["savings_goal"]["pause_largest_subscription_months_to_goal"] == 5

    assert [row["category"] for row in scenario_payload["budgets"]] == [
        "groceries",
        "subscriptions",
        "transport",
        "utilities",
    ]
    assert all(row["over"] is False for row in scenario_payload["budgets"])
    assert scenario_payload["scenarios"][0]["name"] == "baseline_goal_path"
    assert scenario_payload["scenarios"][1]["name"] == "pause_largest_subscription_goal_path"
    assert scenario_payload["scenarios"][1]["affected_subscription"] == "City Gym"
    assert "not financial advice" in scenario_payload["disclaimer"].lower()
    assert "recurring" in summary.lower()
    assert "net worth" in summary.lower()

    bundle_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            out / "manifest.json",
            out / "subscriptions.json",
            out / "finance-scenario.json",
        )
    )
    assert '"transactions"' not in bundle_text
    assert "Synthetic Salary" not in bundle_text
    assert "Synthetic Groceries" not in bundle_text
    assert "bank_credentials_required" in bundle_text


def test_planning_scenario_bundle_is_deterministic(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"

    scenario.write_planning_scenario_bundle(left)
    scenario.write_planning_scenario_bundle(right)

    for name in [
        "manifest.json",
        "subscriptions.json",
        "finance-scenario.json",
        "summary.md",
    ]:
        assert (left / name).read_text(encoding="utf-8") == (
            right / name
        ).read_text(encoding="utf-8")


def test_cli_planning_scenario_writes_bundle(tmp_path, capsys):
    out = tmp_path / "cli-bundle"

    rc = main(["planning-scenario", "--out", str(out)])

    assert rc == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["out_dir"] == str(out)
    assert printed["artifacts"] == [
        "manifest.json",
        "subscriptions.json",
        "finance-scenario.json",
        "summary.md",
    ]
    assert (out / "finance-scenario.json").exists()
