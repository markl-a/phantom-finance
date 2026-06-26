from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_readme_has_public_quickstart_and_disclaimer():
    text = _read("README.md")
    low = text.lower()

    assert "Quickstart" in text
    assert "PHANTOM_FINANCE_HOME" in text
    assert "tests\\fixtures\\bank_en.csv" in text
    assert "phantom_finance.cli report --month 2026-06" in text
    assert "phantom_finance.cli summary --month 2026-06 --json" in text
    assert "phantom_finance.cli scenario-demo --out" in text
    assert "phantom_finance.cli planning-scenario --out" in text
    assert "not financial advice" in low
    assert "docs/PUBLIC_DEMO.md" in text
    assert "docs/LEDGER_AND_SUMMARY_CONTRACT.md" in text
    assert "docs/SUBSCRIPTION_AND_SCENARIO_CONTRACT.md" in text
    assert "docs/PLANNING_SCENARIO_PROOF.md" in text


def test_public_demo_documents_synthetic_data_and_optional_mesh_events():
    text = _read("docs/PUBLIC_DEMO.md")
    low = text.lower()

    assert "synthetic" in low
    assert "PHANTOM_MESH_HOME" in text
    assert "PHANTOM_FINANCE_HOME" in text
    assert "mesh event emission is local and optional" in text
    assert "no live account connection" in low
    assert "scenario-demo" in text
    assert "planning-scenario" in text
    assert "live_account_aggregation=false" in text
    assert "financial_advice=false" in text
    assert "bank_credentials_required=false" in text
    assert "external_network=false" in text
    assert "cloud_llm=false" in text


def test_ledger_and_summary_contract_documents_public_schemas():
    text = _read("docs/LEDGER_AND_SUMMARY_CONTRACT.md")
    low = text.lower()

    assert "ledger.jsonl" in text
    assert "schema_version" in text
    assert "summary --month" in text
    assert "rules.json" in text
    assert "budgets.json" in text
    assert "accounts.json" in text
    assert "bank_en.csv" in text
    assert "aggregate only" in low
    assert "not financial advice" in low


def test_subscription_and_scenario_contract_documents_public_schema():
    text = _read("docs/SUBSCRIPTION_AND_SCENARIO_CONTRACT.md")
    low = text.lower()

    assert "scenario-demo" in text
    assert "manifest.json" in text
    assert "subscriptions.json" in text
    assert "scenario.json" in text
    assert '"schema_version": 1' in text
    assert '"synthetic_only": true' in text
    assert '"live_account_aggregation": false' in text
    assert '"bank_credentials_required": false' in text
    assert '"financial_advice": false' in text
    assert '"raw_transaction_rows_included": false' in text
    assert "not financial advice" in low
    assert "raw transaction rows" in low


def test_planning_scenario_proof_documents_p3_schema():
    text = _read("docs/PLANNING_SCENARIO_PROOF.md")
    low = text.lower()

    assert "planning-scenario" in text
    assert "finance-scenario.json" in text
    assert "subscriptions.json" in text
    assert '"mode": "synthetic_finance_planning_scenario"' in text
    assert '"synthetic_only": true' in text
    assert '"live_account_aggregation": false' in text
    assert '"bank_credentials_required": false' in text
    assert '"financial_advice": false' in text
    assert '"external_network": false' in text
    assert '"cloud_llm": false' in text
    assert '"raw_transaction_rows_included": false' in text
    assert '"budgets"' in text
    assert '"scenarios"' in text
    assert '"disclaimer"' in text
    assert '"monthly_income"' in text
    assert '"subscription_count"' in text
    assert "not financial advice" in low
    assert "net worth" in low
    assert "runway" in low
