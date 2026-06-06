"""Filesystem layout. Everything lives under ~/.phantom-mesh/ like the other satellites.

Override with env vars (used by tests):
  PHANTOM_FINANCE_HOME  -> ledger + budgets   (default ~/.phantom-mesh/finance)
  PHANTOM_MESH_HOME     -> events + logs root (default ~/.phantom-mesh)
"""

from __future__ import annotations

import os
from pathlib import Path


def mesh_home() -> Path:
    return Path(os.environ.get("PHANTOM_MESH_HOME", "~/.phantom-mesh")).expanduser()


def finance_home() -> Path:
    p = Path(
        os.environ.get("PHANTOM_FINANCE_HOME", str(mesh_home() / "finance"))
    ).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def ledger_path() -> Path:
    return finance_home() / "ledger.jsonl"


def budgets_path() -> Path:
    return finance_home() / "budgets.json"


def reports_dir() -> Path:
    p = mesh_home() / "logs" / "phantom-finance"
    p.mkdir(parents=True, exist_ok=True)
    return p


def events_dir() -> Path:
    p = mesh_home() / "events"
    p.mkdir(parents=True, exist_ok=True)
    return p
