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


def _normalize_date(raw: str) -> str:
    """Accept YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD -> ISO."""
    raw = raw.replace("/", "-")
    if "-" not in raw and len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    parts = raw.split("-")
    if len(parts) == 3:
        y, m, d = parts
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    raise ValueError(f"cannot parse date: {raw!r}")
