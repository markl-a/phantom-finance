"""CSV import with header auto-detection (zh + en bank exports)."""

from __future__ import annotations

import csv
from pathlib import Path

from . import categorize, ledger
from .ledger import Transaction, parse_amount

DATE_HEADERS = ["date", "日期", "交易日期", "transaction date"]
AMOUNT_HEADERS = ["amount", "金額", "交易金額"]
DESC_HEADERS = ["description", "desc", "memo", "摘要", "商家", "說明", "merchant"]


def _find(headers: list[str], candidates: list[str]) -> str | None:
    lowered = {h.lower().strip(): h for h in headers}
    for c in candidates:
        if c in lowered:
            return lowered[c]
    return None


def import_csv(path: Path, account: str = "default") -> list[Transaction]:
    """Parse a bank CSV, categorize, append to the ledger. Returns new txns only."""
    with path.open(encoding="utf-8-sig") as f:  # utf-8-sig: TW banks love BOM
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        date_col = _find(headers, DATE_HEADERS)
        amount_col = _find(headers, AMOUNT_HEADERS)
        desc_col = _find(headers, DESC_HEADERS)
        if not (date_col and amount_col and desc_col):
            raise ValueError(
                f"cannot detect columns in {path.name}: headers={headers} "
                f"(need date/amount/description, zh or en)"
            )
        txns = []
        for row in reader:
            raw_amount = (row[amount_col] or "").strip()
            if not raw_amount:
                continue
            txns.append(
                Transaction(
                    date=_normalize_date(row[date_col].strip()),
                    amount=parse_amount(raw_amount),
                    description=(row[desc_col] or "").strip(),
                    account=account,
                )
            )
    categorize.apply(txns)
    return ledger.append(txns)


ROC_EPOCH_OFFSET = 1911  # 民國 year + 1911 = 西元 year (ROC 1 == 1912 CE)


def _normalize_date(raw: str, roc: bool = False) -> str:
    """Accept YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD and 民國 (ROC) years -> ISO.

    ROC (Republic of China / 民國) calendar: ROC year + 1911 = Gregorian year,
    so 115/06/01 -> 2026-06-01. TW bank statements quote the year as a 1-3 digit
    ROC year (e.g. ``115`` or ``115/06/01``); a 4-digit leading field is always
    treated as a western year so existing exports keep parsing unchanged.

    ``roc=True`` is a hint from a bank preset; even without it a leading 1-3
    digit year field is auto-detected as ROC. A 4-digit year is never converted.
    """
    raw = raw.replace("/", "-")
    if "-" not in raw and len(raw) == 8 and raw.isdigit():
        # compact YYYYMMDD — western (TW compact exports use 西元 here)
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    parts = raw.split("-")
    if len(parts) == 3:
        y, m, d = parts
        if y.isdigit() and (roc or len(y.strip()) <= 3):
            # 1-3 digit leading year => ROC year; convert to 西元.
            # (roc=True forces ROC interpretation but a 4-digit year is still
            #  western — there is no valid 4-digit ROC year in real statements.)
            if len(y.strip()) <= 3:
                y = str(int(y) + ROC_EPOCH_OFFSET)
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    raise ValueError(f"cannot parse date: {raw!r}")
