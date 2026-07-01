from decimal import Decimal
from pathlib import Path

import pytest

from phantom_finance import ingest, ledger

FIXTURES = Path(__file__).parent / "fixtures"


def test_import_en_csv():
    written = ingest.import_csv(FIXTURES / "bank_en.csv", account="cathay")
    assert len(written) == 3
    loaded = ledger.load()
    starbucks = next(t for t in loaded if "Starbucks" in t.description)
    assert starbucks.amount == Decimal("-150.50")
    assert starbucks.category == "dining"
    assert starbucks.account == "cathay"


def test_import_zh_csv_with_bom_and_slash_dates():
    written = ingest.import_csv(FIXTURES / "bank_zh.csv")
    assert len(written) == 3
    loaded = ledger.load()
    assert {t.date for t in loaded} == {"2026-06-01", "2026-06-02", "2026-06-03"}
    salary = next(t for t in loaded if t.amount > 0)
    assert salary.category == "income"


def test_reimport_is_idempotent():
    assert len(ingest.import_csv(FIXTURES / "bank_en.csv")) == 3
    assert len(ingest.import_csv(FIXTURES / "bank_en.csv")) == 0
    assert len(ledger.load()) == 3


def test_unknown_headers_raise():
    bad = FIXTURES / "bad_headers.csv"
    with pytest.raises(ValueError, match="cannot detect columns"):
        ingest.import_csv(bad)


def test_normalize_date_formats():
    assert ingest._normalize_date("2026/6/1") == "2026-06-01"
    assert ingest._normalize_date("20260601") == "2026-06-01"
    assert ingest._normalize_date("2026-06-01") == "2026-06-01"
    with pytest.raises(ValueError):
        ingest._normalize_date("June 1st")


def test_normalize_roc_minguo_dates():
    # 民國 (ROC) year = 西元 (Gregorian) year - 1911; 115 -> 2026
    assert ingest._normalize_date("115/06/01") == "2026-06-01"
    assert ingest._normalize_date("115/6/1") == "2026-06-01"
    assert ingest._normalize_date("100/1/1") == "2011-01-01"  # ROC 100 -> 2011
    # western 4-digit years must KEEP working and never be treated as ROC
    assert ingest._normalize_date("2026/06/01") == "2026-06-01"
    assert ingest._normalize_date("2026-06-01") == "2026-06-01"


def test_normalize_date_out_of_range_month():
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("2026-13-01")
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("2026/13/01")


def test_normalize_date_out_of_range_day():
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("2026-01-32")
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("2026/01/32")


def test_normalize_date_compact_out_of_range():
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("20261301")
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("20260132")


def test_normalize_date_zero_month_day():
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("2026-00-01")
    with pytest.raises(ValueError, match="invalid date"):
        ingest._normalize_date("2026-01-00")


def test_normalize_roc_dates_via_explicit_flag():
    # When a preset declares ROC dates, a 2-3 digit leading field is the ROC year.
    assert ingest._normalize_date("115/06/01", roc=True) == "2026-06-01"
    # A western date passed with roc=True is still parsed correctly (4-digit year).
    assert ingest._normalize_date("2026/06/01", roc=True) == "2026-06-01"
