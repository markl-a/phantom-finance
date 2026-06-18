from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from . import paths
from .ledger import Transaction, _atomic_write, _lock


@dataclass
class RecurringCharge:
    merchant: str
    cadence: str
    occurrences: int
    typical_amount: Decimal
    first_date: str
    last_date: str
    latest_amount: Decimal
    price_increased: bool
    pct_change: float


def _norm(desc: str) -> str:
    return " ".join(desc.strip().lower().split())


def charge_key(charge: RecurringCharge) -> str:
    return f"{_norm(charge.merchant)}|{charge.cadence}"


def _classify_cadence(median_gap_days: float) -> str | None:
    if 5 <= median_gap_days <= 9:
        return "weekly"
    if 12 <= median_gap_days <= 16:
        return "biweekly"
    if 26 <= median_gap_days <= 35:
        return "monthly"
    if 85 <= median_gap_days <= 95:
        return "quarterly"
    if 350 <= median_gap_days <= 380:
        return "yearly"
    return None


def _most_common_description(group: list[Transaction]) -> str:
    counts: defaultdict[str, int] = defaultdict(int)
    first_seen: dict[str, int] = {}
    for idx, txn in enumerate(group):
        counts[txn.description] += 1
        first_seen.setdefault(txn.description, idx)
    return max(counts, key=lambda desc: (counts[desc], -first_seen[desc]))


def detect(txns: list[Transaction], min_occurrences: int = 3) -> list[RecurringCharge]:
    grouped: defaultdict[str, list[Transaction]] = defaultdict(list)
    for txn in txns:
        grouped[_norm(txn.description)].append(txn)

    charges = []
    for group in grouped.values():
        if len(group) < min_occurrences:
            continue

        group.sort(key=lambda txn: txn.date)
        dates = [date.fromisoformat(txn.date) for txn in group]
        gaps = [(right - left).days for left, right in zip(dates, dates[1:])]
        median_gap = statistics.median(gaps)
        cadence = _classify_cadence(float(median_gap))
        if cadence is None:
            continue

        abs_amounts = sorted(abs(txn.amount) for txn in group)
        typical_amount = statistics.median(abs_amounts)
        earliest_abs = abs(group[0].amount)
        latest_abs = abs(group[-1].amount)
        price_increased = latest_abs > earliest_abs
        pct_change = (
            float((latest_abs - earliest_abs) / earliest_abs * Decimal("100"))
            if earliest_abs != 0
            else 0.0
        )

        charges.append(
            RecurringCharge(
                merchant=_most_common_description(group),
                cadence=cadence,
                occurrences=len(group),
                typical_amount=typical_amount,
                first_date=group[0].date,
                last_date=group[-1].date,
                latest_amount=latest_abs,
                price_increased=price_increased,
                pct_change=pct_change,
            )
        )

    return sorted(
        charges,
        key=lambda charge: (
            -date.fromisoformat(charge.last_date).toordinal(),
            charge.merchant,
        ),
    )


def price_hikes(txns: list[Transaction], min_occurrences: int = 3) -> list[RecurringCharge]:
    return [
        charge
        for charge in detect(txns, min_occurrences=min_occurrences)
        if charge.price_increased and round(charge.pct_change) > 0
    ]


def load_store(path: Path | None = None) -> dict[str, dict]:
    p = path or paths.recurring_path()
    if not p.exists():
        return {}
    raw = p.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    try:
        store = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid recurring file {p}: {e.msg}") from e
    if not isinstance(store, dict):
        raise ValueError(f"invalid recurring file {p}: expected JSON object")
    return store


def upsert(charges: list[RecurringCharge], path: Path | None = None) -> dict[str, dict]:
    p = path or paths.recurring_path()
    with _lock(p):
        store = load_store(p)
        for charge in charges:
            key = charge_key(charge)
            hiked = charge.price_increased and round(charge.pct_change) > 0
            if key not in store:
                store[key] = {
                    "status": "new",
                    "reviewed_at": None,
                }
            else:
                old_amount = store[key].get("amount")
                if hiked and str(charge.latest_amount) != old_amount:
                    store[key]["status"] = "new"
                    store[key]["reviewed_at"] = None
            store[key].update(
                {
                    "key": key,
                    "description": charge.merchant,
                    "cadence": charge.cadence,
                    "amount": str(charge.latest_amount),
                    "last_seen": charge.last_date,
                    "price_hike_pct": round(charge.pct_change, 2),
                }
            )
        _atomic_write(
            p,
            [json.dumps(store, indent=2, sort_keys=True, ensure_ascii=False)],
        )
        return store


def review(key: str, status: str, path: Path | None = None) -> dict:
    if status not in {"new", "reviewed", "ignored"}:
        raise ValueError(f"invalid recurring status: {status}")
    p = path or paths.recurring_path()
    with _lock(p):
        store = load_store(p)
        if key not in store:
            raise KeyError(f"unknown recurring charge: {key}")
        store[key]["status"] = status
        store[key]["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_write(
            p,
            [json.dumps(store, indent=2, sort_keys=True, ensure_ascii=False)],
        )
        return store[key]


def list_items(status: str | None = None, path: Path | None = None) -> list[dict]:
    items = list(load_store(path).values())
    if status:
        items = [it for it in items if it["status"] == status]
    items = sorted(items, key=lambda it: it["description"])
    return sorted(items, key=lambda it: it["last_seen"], reverse=True)
