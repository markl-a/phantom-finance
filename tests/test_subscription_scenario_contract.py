from __future__ import annotations

import json

from phantom_finance import scenario
from phantom_finance.cli import main


def test_subscription_scenario_bundle_is_synthetic_aggregate_only(tmp_path):
    out = tmp_path / "scenario"

    result = scenario.write_scenario_demo_bundle(out)

    assert result == out
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    subscriptions = json.loads((out / "subscriptions.json").read_text(encoding="utf-8"))
    scenario_payload = json.loads((out / "scenario.json").read_text(encoding="utf-8"))
    summary = (out / "summary.md").read_text(encoding="utf-8")

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_subscription_scenario_loop"
    assert manifest["synthetic_only"] is True
    assert manifest["live_account_aggregation"] is False
    assert manifest["bank_credentials_required"] is False
    assert manifest["financial_advice"] is False
    assert manifest["external_network"] is False
    assert manifest["cloud_llm"] is False
    assert manifest["artifacts"] == [
        "manifest.json",
        "subscriptions.json",
        "scenario.json",
        "summary.md",
    ]

    assert subscriptions["schema_version"] == 1
    assert subscriptions["data_policy"] == "synthetic_only"
    assert subscriptions["raw_transaction_rows_included"] is False
    assert subscriptions["subscriptions"]
    assert all("transactions" not in row for row in subscriptions["subscriptions"])
    assert all("description" not in row for row in subscriptions["subscriptions"])
    assert any(row["price_increased"] for row in subscriptions["subscriptions"])
    assert [row["label"] for row in subscriptions["subscriptions"]] == [
        "City Gym",
        "StreamFlix",
        "CloudBox",
    ]

    assert scenario_payload["schema_version"] == 1
    assert scenario_payload["horizon_months"] == 3
    assert scenario_payload["financial_advice"] is False
    assert scenario_payload["live_account_aggregation"] is False
    assert scenario_payload["raw_transaction_rows_included"] is False
    assert scenario_payload["summary"]["month"] == "2026-06"
    assert scenario_payload["summary"]["net"] == "42030"
    assert scenario_payload["summary"]["subscription_count"] == 3
    assert scenario_payload["summary"]["subscription_latest_total"] == "1970"
    assert scenario_payload["scenarios"][0]["name"] == "baseline"
    assert scenario_payload["scenarios"][1]["name"] == "pause_largest_subscription"
    assert scenario_payload["scenarios"][1]["affected_subscription"] == "City Gym"
    assert "not financial advice" in scenario_payload["disclaimer"].lower()

    bundle_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (out / "manifest.json", out / "subscriptions.json", out / "scenario.json")
    )
    assert "transactions" not in bundle_text
    assert "raw transaction" not in bundle_text.lower().replace("raw_transaction_rows_included", "")
    assert "Card " not in bundle_text
    assert "Synthetic Salary" not in bundle_text
    assert "not financial advice" in summary.lower()


def test_subscription_scenario_bundle_is_deterministic(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"

    scenario.write_scenario_demo_bundle(left)
    scenario.write_scenario_demo_bundle(right)

    for name in ["manifest.json", "subscriptions.json", "scenario.json", "summary.md"]:
        assert (left / name).read_text(encoding="utf-8") == (
            right / name
        ).read_text(encoding="utf-8")


def test_cli_scenario_demo_writes_bundle(tmp_path, capsys):
    out = tmp_path / "cli-bundle"

    rc = main(["scenario-demo", "--out", str(out)])

    assert rc == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["out_dir"] == str(out)
    assert printed["artifacts"] == [
        "manifest.json",
        "subscriptions.json",
        "scenario.json",
        "summary.md",
    ]
    assert (out / "scenario.json").exists()
