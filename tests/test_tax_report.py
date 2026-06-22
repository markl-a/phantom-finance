from decimal import Decimal

from phantom_finance import reporter
from phantom_finance.ledger import Transaction


def _txns():
    return [
        Transaction(date="2026-06-03", amount=Decimal("30000"), description="A公司 程式接案", category="income"),
        Transaction(date="2026-06-10", amount=Decimal("8000"), description="出版社 版稅", category="income"),
        Transaction(date="2026-06-12", amount=Decimal("-899"), description="中華電信", category="utilities"),
        Transaction(date="2026-06-15", amount=Decimal("-160"), description="星巴克", category="dining"),
    ]


def test_tax_summary_splits_income_by_type():
    s = reporter.tax_summary(_txns(), "2026-06")
    assert s["income_by_type"]["9A"] == Decimal("30000")
    assert s["income_by_type"]["9B"] == Decimal("8000")
    assert Decimal("899") in [amt for _, amt in s["deductible_candidates"]]
    assert s["nhi_supplement_count"] == 1  # the 30000 9A payment


def test_render_includes_tax_section():
    md = reporter.render(_txns(), "2026-06")
    assert "報稅摘要" in md
    assert "9A" in md
    assert "可扣抵候選" in md
    # safety: it is prep, not advice
    assert "非稅務建議" in md


from phantom_finance import paths


def test_quarter_months_expands_correctly():
    assert reporter.quarter_months("2026Q2") == ["2026-04", "2026-05", "2026-06"]


def test_write_quarter_report_aggregates_three_months(monkeypatch):
    txns = [
        Transaction(date="2026-04-10", amount=Decimal("30000"), description="接案", category="income"),
        Transaction(date="2026-06-10", amount=Decimal("20000"), description="顧問費", category="income"),
    ]
    out = reporter.write_quarter_report("2026Q2", txns=txns)
    assert out.exists()
    body = out.read_text(encoding="utf-8")
    assert "2026Q2" in body
    assert "報稅摘要" in body
    assert "50000" in body  # 9A income aggregated across the quarter
