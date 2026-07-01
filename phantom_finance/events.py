"""Emit events into ~/.phantom-mesh/events/ so phantom-companion can consume them.

Same spirit as the other satellites: one directory per event with meta.json.
Companion correlation (spend vs mood/productivity) is Tier 2 on its side.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from . import paths


def emit(kind: str, payload: dict) -> str:
    """Write an event, return the event id."""
    ts = datetime.now(timezone.utc)
    base_event_id = f"{ts.strftime('%Y%m%dT%H%M%S')}-phantom-finance-{kind}"
    event_root = paths.events_dir()
    suffix = 0
    while True:
        event_id = (
            base_event_id if suffix == 0 else f"{base_event_id}-{suffix:04d}"
        )
        event_dir = event_root / event_id
        try:
            event_dir.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            suffix += 1
    meta = {
        "source": "phantom-finance",
        "kind": kind,
        "ts": ts.isoformat(),
        "payload": payload,
    }
    (event_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return event_id
