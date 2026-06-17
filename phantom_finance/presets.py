"""Named column-mapping presets for major Taiwan bank CSV statement exports.

Scope / honesty
---------------
These presets are **column-mapping scaffolds** built from PUBLIC, documented
TW-bank statement layouts (the published header labels banks use in their
online-banking CSV / 對帳單 exports). They were authored WITHOUT any real
account data and are validated only against the small hand-authored synthetic
fixtures in ``tests/fixtures/tw_*.csv``. Validation against a real — even
redacted — bank statement is still pending and owner-blocked; do not treat a
preset as field-verified against a live export.

Each preset declares, for one bank:

* the header-label **variants** that map onto the canonical fields
  ``date`` / ``amount`` / ``description`` (banks reword headers across product
  lines and export versions, so each canonical field accepts several labels);
* the **sign convention** — ``"signed"`` (one amount column, negative = expense)
  vs ``"two_column"`` (separate credit/debit columns, e.g. 支出/存入);
* the **date form** — ``"roc"`` (民國 year, ROC + 1911 = 西元) vs ``"western"``;
* ``skip_rows`` — leading title / metadata rows that sit ABOVE the real header
  row in some exports (e.g. E.SUN prints a bank name + 查詢區間 banner first);
* thousands-separator / ``NT$`` handling is delegated to
  :func:`phantom_finance.ledger.parse_amount`, which already strips ``,`` /
  ``NT$`` / ``$`` / ``元`` — recorded here as ``money_note`` for documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Preset:
    name: str
    sign_convention: str  # "signed" | "two_column"
    date_form: str  # "roc" | "western"
    date_headers: list[str] = field(default_factory=list)
    desc_headers: list[str] = field(default_factory=list)
    # signed single-column banks use amount_headers; two-column banks use the pair
    amount_headers: list[str] = field(default_factory=list)
    credit_headers: list[str] = field(default_factory=list)  # 存入 / 收入 -> positive
    debit_headers: list[str] = field(default_factory=list)  # 支出 / 提出 -> negative
    skip_rows: int = 0
    money_note: str = "thousands-sep + NT$/$/元 stripped by ledger.parse_amount"

    @property
    def is_roc(self) -> bool:
        return self.date_form == "roc"

    @property
    def is_two_column(self) -> bool:
        return self.sign_convention == "two_column"


# Public documented header layouts. Variants are lowercased on match in ingest,
# but stored here as banks print them (zh labels are case-stable anyway).
PRESETS: dict[str, Preset] = {
    # 國泰世華 Cathay United — single signed amount column, 西元 dates.
    "cathay": Preset(
        name="cathay",
        sign_convention="signed",
        date_form="western",
        date_headers=["交易日期", "日期", "transaction date", "date"],
        desc_headers=["摘要", "說明", "交易說明", "description", "memo"],
        amount_headers=["金額", "交易金額", "amount"],
    ),
    # 中國信託 CTBC — separate 支出 / 存入 columns, 民國 (ROC) dates.
    "ctbc": Preset(
        name="ctbc",
        sign_convention="two_column",
        date_form="roc",
        date_headers=["日期", "交易日期", "date"],
        desc_headers=["摘要", "說明", "備註", "description"],
        debit_headers=["支出", "提領", "扣款", "debit", "withdrawal"],
        credit_headers=["存入", "存款", "credit", "deposit"],
    ),
    # 玉山 E.SUN — single signed amount, 民國 dates, leading banner rows to skip.
    "esun": Preset(
        name="esun",
        sign_convention="signed",
        date_form="roc",
        date_headers=["交易日", "交易日期", "日期", "date"],
        desc_headers=["說明", "摘要", "交易說明", "description"],
        amount_headers=["金額", "交易金額", "amount"],
        skip_rows=2,  # bank-name banner + 帳號/查詢區間 line precede the header
    ),
    # 台新 Taishin — separate 提出 / 存入 columns, 西元 dates.
    "taishin": Preset(
        name="taishin",
        sign_convention="two_column",
        date_form="western",
        date_headers=["交易日期", "日期", "date"],
        desc_headers=["摘要", "說明", "備註", "description"],
        debit_headers=["提出", "支出", "轉出", "debit"],
        credit_headers=["存入", "轉入", "credit"],
    ),
}

# Friendly aliases users may type on the CLI / pass to import_csv(bank=...).
_ALIASES: dict[str, str] = {
    "e.sun": "esun",
    "esun bank": "esun",
    "玉山": "esun",
    "國泰世華": "cathay",
    "cathay united": "cathay",
    "中國信託": "ctbc",
    "台新": "taishin",
}


def names() -> list[str]:
    """Canonical preset names (for the CLI choices)."""
    return sorted(PRESETS)


def get(name: str) -> Preset:
    """Look up a preset by canonical name or friendly alias (case-insensitive).

    Raises KeyError on an unknown bank.
    """
    key = (name or "").strip().lower()
    key = _ALIASES.get(key, key)
    try:
        return PRESETS[key]
    except KeyError as e:
        raise KeyError(
            f"unknown bank preset {name!r}; known: {', '.join(names())}"
        ) from e
