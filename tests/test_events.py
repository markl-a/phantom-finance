import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from phantom_finance import events, paths


class FixedDatetime:
    @classmethod
    def now(cls, tz):
        return datetime(2026, 7, 1, 12, 30, 5, tzinfo=timezone.utc)


def test_emit_same_second_events_get_distinct_dirs_without_overwrite(monkeypatch):
    monkeypatch.setattr(events, "datetime", FixedDatetime)

    first = events.emit("monthly-report", {"ordinal": 1})
    second = events.emit("monthly-report", {"ordinal": 2})

    assert first != second
    assert sorted(p.name for p in paths.events_dir().iterdir()) == [first, second]

    first_meta = json.loads(
        (paths.events_dir() / first / "meta.json").read_text(encoding="utf-8")
    )
    second_meta = json.loads(
        (paths.events_dir() / second / "meta.json").read_text(encoding="utf-8")
    )
    assert first_meta["payload"] == {"ordinal": 1}
    assert second_meta["payload"] == {"ordinal": 2}
