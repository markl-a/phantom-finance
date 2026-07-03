from __future__ import annotations

import datetime
import statistics
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from .ledger import Transaction


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


def charge_key(charge: "RecurringCharge") -> str:
    """Stable identity for a detected charge across re-detections.

    ``detect`` groups transactions by the normalised description, so the
    normalised merchant is the same group key on every run even as amounts,
    dates and occurrence counts drift. Used as the persistence key in
    ``recurring_store``.
    """
    return _norm(charge.merchant)


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
        dates = [datetime.date.fromisoformat(txn.date) for txn in group]
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
            -datetime.date.fromisoformat(charge.last_date).toordinal(),
            charge.merchant,
        ),
    )


def price_hikes(txns: list[Transaction], min_occurrences: int = 3) -> list[RecurringCharge]:
    return [
        charge
        for charge in detect(txns, min_occurrences=min_occurrences)
        if charge.price_increased and round(charge.pct_change) > 0
    ]
