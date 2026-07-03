"""Persistence + review workflow for detected recurring charges.

Detection lives in :mod:`recurring` and is stateless. This module remembers
the *review decision* the user has made about each recurring charge across
runs, in a ``recurring.json`` store under the finance data dir.

Each charge moves through a small state machine::

    new ──review──▶ reviewed
     │  ◀──reset──┘  │
     │               ignore
     ├──ignore──▶ ignored
                    │
     ◀────reset─────┤
     reviewed ◀─review┘

- ``new``      freshly detected, the user has not looked at it yet
- ``reviewed`` the user has acknowledged it as a real recurring charge
- ``ignored``  the user has dismissed it (not a subscription they track)

``sync`` folds a fresh detection pass into the store: brand-new charges are
recorded as ``new``, while charges that already exist keep their review state
and only have their detection fields (amounts / dates / occurrences / price
hike) refreshed. A user's ``reviewed`` / ``ignored`` decision therefore
survives re-detection and never silently reverts to ``new``.
"""

from __future__ import annotations

import datetime
import json
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from . import paths, recurring
from .recurring import RecurringCharge

NEW = "new"
REVIEWED = "reviewed"
IGNORED = "ignored"
STATES: tuple[str, ...] = (NEW, REVIEWED, IGNORED)

# Allowed state-machine transitions (same-state is always a no-op).
_TRANSITIONS: dict[str, set[str]] = {
    NEW: {REVIEWED, IGNORED},
    REVIEWED: {IGNORED, NEW},
    IGNORED: {REVIEWED, NEW},
}


@dataclass
class RecurringRecord:
    key: str
    merchant: str
    cadence: str
    state: str
    occurrences: int
    typical_amount: Decimal
    latest_amount: Decimal
    first_date: str
    last_date: str
    price_increased: bool
    pct_change: float
    first_seen: str  # ISO-8601 UTC timestamp: when first persisted
    last_updated: str  # ISO-8601 UTC timestamp: last detection refresh / transition

    def to_dict(self) -> dict[str, object]:
        return {
            "merchant": self.merchant,
            "cadence": self.cadence,
            "state": self.state,
            "occurrences": self.occurrences,
            "typical_amount": str(self.typical_amount),
            "latest_amount": str(self.latest_amount),
            "first_date": self.first_date,
            "last_date": self.last_date,
            "price_increased": self.price_increased,
            "pct_change": self.pct_change,
            "first_seen": self.first_seen,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, key: str, data: dict[str, object]) -> "RecurringRecord":
        state = str(data.get("state", NEW))
        if state not in STATES:
            raise ValueError(f"recurring record {key!r} has unknown state {state!r}")
        return cls(
            key=key,
            merchant=str(data.get("merchant", key)),
            cadence=str(data.get("cadence", "")),
            state=state,
            occurrences=int(data.get("occurrences", 0)),
            typical_amount=Decimal(str(data.get("typical_amount", "0"))),
            latest_amount=Decimal(str(data.get("latest_amount", "0"))),
            first_date=str(data.get("first_date", "")),
            last_date=str(data.get("last_date", "")),
            price_increased=bool(data.get("price_increased", False)),
            pct_change=float(data.get("pct_change", 0.0)),
            first_seen=str(data.get("first_seen", "")),
            last_updated=str(data.get("last_updated", "")),
        )


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def load(path: Path | None = None) -> dict[str, RecurringRecord]:
    p = path or paths.recurring_path()
    if not p.exists():
        return {}

    raw_text = p.read_text(encoding="utf-8")
    if not raw_text.strip():
        # a truncated / half-written file is treated as "no records", not a crash
        return {}

    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid recurring file {p}: {e.msg}") from e

    if not isinstance(raw, dict):
        raise ValueError(f"recurring file {p} must be a JSON object of key -> record")

    return {str(k): RecurringRecord.from_dict(str(k), v) for k, v in raw.items()}


def save(records: dict[str, RecurringRecord], path: Path | None = None) -> None:
    p = path or paths.recurring_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {key: records[key].to_dict() for key in sorted(records)}
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"

    # atomic write so a crash mid-save can't leave a half-written store
    tmp = p.with_name(p.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp), str(p))


def sync(
    charges: list[RecurringCharge],
    path: Path | None = None,
    now: str | None = None,
) -> dict[str, RecurringRecord]:
    """Merge a fresh detection pass into the store and persist it.

    New charges are recorded as ``new``; existing charges keep their review
    state and only have their detection fields refreshed. Records that are no
    longer detected are *kept* (an ``ignored`` charge that drops out of the
    detection window must not resurface as ``new`` later).
    """
    p = path or paths.recurring_path()
    stamp = now or _now()
    records = load(p)

    for charge in charges:
        key = recurring.charge_key(charge)
        existing = records.get(key)
        if existing is None:
            records[key] = RecurringRecord(
                key=key,
                merchant=charge.merchant,
                cadence=charge.cadence,
                state=NEW,
                occurrences=charge.occurrences,
                typical_amount=charge.typical_amount,
                latest_amount=charge.latest_amount,
                first_date=charge.first_date,
                last_date=charge.last_date,
                price_increased=charge.price_increased,
                pct_change=charge.pct_change,
                first_seen=stamp,
                last_updated=stamp,
            )
        else:
            # refresh detection fields, preserve the user's review decision
            existing.merchant = charge.merchant
            existing.cadence = charge.cadence
            existing.occurrences = charge.occurrences
            existing.typical_amount = charge.typical_amount
            existing.latest_amount = charge.latest_amount
            existing.first_date = charge.first_date
            existing.last_date = charge.last_date
            existing.price_increased = charge.price_increased
            existing.pct_change = charge.pct_change
            existing.last_updated = stamp

    save(records, p)
    return records


def set_state(
    key: str,
    state: str,
    path: Path | None = None,
    now: str | None = None,
) -> RecurringRecord:
    """Transition one record to ``state`` and persist. Returns the record.

    Raises ``ValueError`` for an unknown target state, an unknown key, or a
    transition the state machine disallows. Setting the current state is an
    idempotent no-op.
    """
    if state not in STATES:
        raise ValueError(f"unknown recurring state {state!r}; expected one of {', '.join(STATES)}")

    p = path or paths.recurring_path()
    records = load(p)
    record = records.get(key)
    if record is None:
        raise ValueError(f"no recurring charge with key {key!r}")

    if record.state != state:
        if state not in _TRANSITIONS[record.state]:
            raise ValueError(f"cannot move recurring charge from {record.state!r} to {state!r}")
        record.state = state
        record.last_updated = now or _now()
        save(records, p)

    return record


def review(key: str, path: Path | None = None, now: str | None = None) -> RecurringRecord:
    return set_state(key, REVIEWED, path=path, now=now)


def ignore(key: str, path: Path | None = None, now: str | None = None) -> RecurringRecord:
    return set_state(key, IGNORED, path=path, now=now)


def reset(key: str, path: Path | None = None, now: str | None = None) -> RecurringRecord:
    return set_state(key, NEW, path=path, now=now)


def resolve_key(query: str, records: dict[str, RecurringRecord]) -> str:
    """Resolve a user-supplied merchant string to exactly one stored key.

    Tries, in order: exact key, exact (case-insensitive) merchant, then a
    unique case-insensitive substring of the key or merchant. Raises
    ``ValueError`` when nothing matches or the match is ambiguous.
    """
    q = query.strip().lower()
    if q in records:
        return q

    exact = [k for k, r in records.items() if r.merchant.lower() == q]
    if len(exact) == 1:
        return exact[0]

    subs = [k for k, r in records.items() if q in k or q in r.merchant.lower()]
    if len(subs) == 1:
        return subs[0]
    if not subs:
        raise ValueError(f"no recurring charge matches {query!r}")
    matches = ", ".join(sorted(records[k].merchant for k in subs))
    raise ValueError(f"ambiguous recurring charge {query!r}; matches: {matches}")
