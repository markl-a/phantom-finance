"""Tests for filesystem layout and home overrides."""

from __future__ import annotations

from pathlib import Path
from phantom_finance.paths import (
    mesh_home,
    finance_home,
    ledger_path,
    budgets_path,
    reports_dir,
    events_dir,
)


def test_paths_override_and_creation(tmp_path: Path, monkeypatch):
    custom_mesh = tmp_path / "custom_mesh"
    custom_finance = tmp_path / "custom_finance"

    # Set env vars via monkeypatch
    monkeypatch.setenv("PHANTOM_MESH_HOME", str(custom_mesh))
    monkeypatch.setenv("PHANTOM_FINANCE_HOME", str(custom_finance))

    # Assert directories are NOT created yet
    assert not custom_mesh.exists()
    assert not custom_finance.exists()

    # Call mesh_home and finance_home
    assert mesh_home() == custom_mesh
    # Calling finance_home should auto-create the finance home directory
    assert finance_home() == custom_finance
    assert custom_finance.is_dir()

    # ledger_path and budgets_path should resolve under custom_finance
    assert ledger_path() == custom_finance / "ledger.jsonl"
    assert budgets_path() == custom_finance / "budgets.json"

    # reports_dir should resolve under custom_mesh and be auto-created
    rep_dir = reports_dir()
    assert rep_dir == custom_mesh / "logs" / "phantom-finance"
    assert rep_dir.is_dir()

    # events_dir should resolve under custom_mesh and be auto-created
    evt_dir = events_dir()
    assert evt_dir == custom_mesh / "events"
    assert evt_dir.is_dir()
