"""Tests for the TW-bank CSV presets (column-mapping scaffolds).

IMPORTANT: every fixture here is HAND-AUTHORED from PUBLIC documented header
shapes. No real account data, no real statement was used. Validation against a
real (even redacted) statement is still pending — see README Tier-2 note.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from phantom_finance import ingest, ledger, presets

FIXTURES = Path(__file__).parent / "fixtures"


def test_preset_registry_has_the_four_banks():
    for name in ("cathay", "ctbc", "esun", "taishin"):
        p = presets.get(name)
        assert p.name == name
        # every preset must declare its canonical-field mapping + conventions
        assert p.date_headers, f"{name}: no date headers"
        assert p.desc_headers, f"{name}: no description headers"
        # either a single signed amount col OR a credit/debit pair
        if p.sign_convention == "signed":
            assert p.amount_headers
        else:
            assert p.credit_headers and p.debit_headers


def test_preset_lookup_is_case_insensitive_and_rejects_unknown():
    assert presets.get("CATHAY").name == "cathay"
    assert presets.get("E.SUN").name == "esun"  # friendly alias
    with pytest.raises(KeyError):
        presets.get("not-a-bank")


# --- synthetic round-trip per bank -----------------------------------------

def test_cathay_signed_western_roundtrip():
    # Cathay 國泰世華: single signed amount column, 西元 dates, NT$/thousands sep
    written = ingest.import_csv(FIXTURES / "tw_cathay.csv", account="cathay", bank="cathay")
    assert len(written) == 3
    loaded = ledger.load()
    by_desc = {t.description: t for t in loaded}
    assert by_desc["全聯福利中心"].amount == Decimal("-880")
    assert by_desc["全聯福利中心"].date == "2026-06-01"
    assert by_desc["星巴克信義"].amount == Decimal("-150.50")
    # positive amount = income kept positive
    salary = next(t for t in loaded if t.amount > 0)
    assert salary.amount == Decimal("48000")
    assert salary.category == "income"


def test_ctbc_two_column_roc_roundtrip():
    # CTBC 中國信託: separate 支出/存入 (debit/credit) cols, 民國 dates
    written = ingest.import_csv(FIXTURES / "tw_ctbc.csv", account="ctbc", bank="ctbc")
    assert len(written) == 3
    loaded = ledger.load()
    by_desc = {t.description: t for t in loaded}
    # debit column -> negative signed amount
    assert by_desc["家樂福內湖"].amount == Decimal("-1200")
    assert by_desc["家樂福內湖"].date == "2026-06-02"  # 115/06/02 ROC -> 2026
    # credit column -> positive signed amount
    assert by_desc["六月薪資"].amount == Decimal("48000")
    assert by_desc["六月薪資"].category == "income"


def test_esun_signed_roc_roundtrip():
    # E.SUN 玉山: single signed amount, 民國 dates, header rows to skip
    written = ingest.import_csv(FIXTURES / "tw_esun.csv", account="esun", bank="esun")
    assert len(written) == 2
    loaded = ledger.load()
    by_desc = {t.description: t for t in loaded}
    assert by_desc["麥當勞"].amount == Decimal("-99")
    assert by_desc["麥當勞"].date == "2026-06-05"  # 115/06/05
    assert by_desc["利息"].amount == Decimal("12.34")


def test_taishin_two_column_western_roundtrip():
    # Taishin 台新: separate 提出/存入 cols, 西元 dates
    written = ingest.import_csv(FIXTURES / "tw_taishin.csv", account="taishin", bank="taishin")
    assert len(written) == 2
    loaded = ledger.load()
    by_desc = {t.description: t for t in loaded}
    assert by_desc["中華電信"].amount == Decimal("-599")
    assert by_desc["股息"].amount == Decimal("1000")


def test_unknown_bank_name_raises():
    with pytest.raises(KeyError):
        ingest.import_csv(FIXTURES / "tw_cathay.csv", bank="nonexistent-bank")


def test_no_bank_flag_keeps_autodetect_behavior():
    # the EXISTING en fixture must still import with no --bank (auto-detect path)
    written = ingest.import_csv(FIXTURES / "bank_en.csv", account="cathay")
    assert len(written) == 3
