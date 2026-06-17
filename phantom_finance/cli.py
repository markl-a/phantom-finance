"""phantom-finance CLI.

  phantom-finance add -- -120 "全聯 groceries"      # expense (signed amount)
  phantom-finance import statement.csv --account cathay
  phantom-finance report --month 2026-06
  phantom-finance budget set dining 6000
  phantom-finance budget show --month 2026-06
  phantom-finance recat
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import budget, categorize, ingest, ledger, presets, recurring, reporter
from .ledger import Transaction, parse_amount


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phantom-finance")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="add one transaction (negative = expense)")
    p_add.add_argument("amount")
    p_add.add_argument("description")
    p_add.add_argument("--date", default=date.today().isoformat())
    p_add.add_argument("--account", default="default")
    p_add.add_argument("--category", default=None)

    p_imp = sub.add_parser("import", help="import a bank CSV")
    p_imp.add_argument("csv_path", type=Path)
    p_imp.add_argument("--account", default="default")
    p_imp.add_argument(
        "--bank",
        default=None,
        choices=presets.names(),
        help="use a named TW-bank preset (default: auto-detect headers)",
    )

    p_rep = sub.add_parser("report", help="write the monthly report")
    p_rep.add_argument("--month", default=date.today().isoformat()[:7])

    p_bud = sub.add_parser("budget", help="set / show monthly budgets")
    bud_sub = p_bud.add_subparsers(dest="budget_cmd", required=True)
    p_set = bud_sub.add_parser("set")
    p_set.add_argument("category")
    p_set.add_argument("limit")
    p_show = bud_sub.add_parser("show")
    p_show.add_argument("--month", default=date.today().isoformat()[:7])

    sub.add_parser("recat", help="re-run the categorizer on uncategorized txns")

    sub.add_parser("recurring", help="list detected recurring charges / subscriptions")

    args = parser.parse_args(argv)

    if args.cmd == "add":
        txn = Transaction(
            date=args.date,
            amount=parse_amount(args.amount),
            description=args.description,
            account=args.account,
        )
        txn.category = args.category or categorize.categorize_one(txn)
        written = ledger.append([txn])
        print(f"added {len(written)} txn ({txn.category})" if written else "duplicate, skipped")

    elif args.cmd == "import":
        written = ingest.import_csv(args.csv_path, account=args.account, bank=args.bank)
        print(f"imported {len(written)} new transactions from {args.csv_path.name}")

    elif args.cmd == "report":
        out = reporter.write_report(args.month)
        print(f"report written: {out}")

    elif args.cmd == "budget" and args.budget_cmd == "set":
        budgets = budget.load()
        budgets[args.category] = Decimal(args.limit)
        budget.save(budgets)
        print(f"budget set: {args.category} = {args.limit}/month")

    elif args.cmd == "budget" and args.budget_cmd == "show":
        statuses = budget.check(ledger.load(), args.month)
        if not statuses:
            print("no budgets set — try: phantom-finance budget set dining 6000")
        for st in statuses:
            mark = "over plan" if st.over else "ok"
            print(f"{st.category:15s} {st.spent:>10} / {st.limit:<10} {st.ratio:>5.0%}  {mark}")

    elif args.cmd == "recat":
        txns = ledger.load()
        changed = categorize.apply(txns)
        ledger.rewrite(txns)
        print(f"re-categorized {changed} transactions")

    elif args.cmd == "recurring":
        charges = recurring.detect(ledger.load())
        if not charges:
            print("no recurring charges detected yet")
        for c in charges:
            line = (
                f"{c.merchant:24s} {c.cadence:9s} x{c.occurrences:<3d} "
                f"~{c.typical_amount} latest {c.latest_amount}"
            )
            if c.price_increased:
                line += f"  PRICE UP +{c.pct_change:.0f}%"
            print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
