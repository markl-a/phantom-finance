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

from . import budget, categorize, ingest, ledger, llm, networth, presets, recurring, reporter
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

    p_acc = sub.add_parser("account", help="manage account types")
    acc_sub = p_acc.add_subparsers(dest="account_cmd", required=True)
    p_acc_add = acc_sub.add_parser("add")
    p_acc_add.add_argument("name")
    p_acc_add.add_argument("--type", dest="account_type", choices=["cash", "asset"], required=True)
    p_acc_add.add_argument("--currency", default="TWD")
    acc_sub.add_parser("list")
    p_acc_set = acc_sub.add_parser("set-type")
    p_acc_set.add_argument("name")
    p_acc_set.add_argument("account_type", choices=["cash", "asset"])

    sub.add_parser("recat", help="re-run the categorizer on uncategorized txns")

    p_rec = sub.add_parser(
        "recurring",
        help="detect + persist recurring charges; review them",
    )
    rec_sub = p_rec.add_subparsers(dest="recurring_cmd", required=False)
    p_rec_rev = rec_sub.add_parser(
        "review",
        help="set review status for a recurring charge",
    )
    p_rec_rev.add_argument("key")
    p_rec_rev.add_argument(
        "--status",
        choices=["new", "reviewed", "ignored"],
        default="reviewed",
    )
    p_rec_list = rec_sub.add_parser("list", help="list persisted recurring charges")
    p_rec_list.add_argument(
        "--status",
        choices=["new", "reviewed", "ignored"],
        default=None,
    )

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

    elif args.cmd == "account" and args.account_cmd == "add":
        networth.save_account(args.name, args.account_type, args.currency)
        print(f"account added: {args.name} ({args.account_type.lower()}, {args.currency})")

    elif args.cmd == "account" and args.account_cmd == "list":
        accounts = networth.load_accounts()
        if not accounts:
            print("no accounts configured yet")
        for name in sorted(accounts):
            account = accounts[name]
            print(f"{name}  {account['type']}  {account['currency']}")

    elif args.cmd == "account" and args.account_cmd == "set-type":
        try:
            networth.set_account_type(args.name, args.account_type)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"account {args.name} type set to {args.account_type.lower()}")

    elif args.cmd == "recat":
        txns = ledger.load()
        changed = categorize.apply(txns, llm=llm.make_categorizer())
        ledger.rewrite(txns)
        print(f"re-categorized {changed} transactions")

    elif args.cmd == "recurring" and getattr(args, "recurring_cmd", None) == "review":
        try:
            item = recurring.review(args.key, args.status)
        except KeyError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"{item['key']}  status -> {item['status']}")

    elif args.cmd == "recurring" and getattr(args, "recurring_cmd", None) == "list":
        items = recurring.list_items(args.status)
        if not items:
            print("no recurring charges stored yet")
        for it in items:
            line = (
                f"{it['key']:32s} {it['status']:8s} {it['cadence']:9s} "
                f"~{it['amount']} last {it['last_seen']}"
            )
            if round(it["price_hike_pct"]) > 0:
                line += f"  PRICE UP +{it['price_hike_pct']:.0f}%"
            print(line)

    elif args.cmd == "recurring":
        charges = recurring.detect(ledger.load())
        store = recurring.upsert(charges)
        if not charges:
            print("no recurring charges detected yet")
        for c in charges:
            key = recurring.charge_key(c)
            it = store.get(key, {})
            line = (
                f"{key:32s} {it.get('status', 'new'):8s} {c.cadence:9s} "
                f"x{c.occurrences:<3d} "
                f"~{c.typical_amount} latest {c.latest_amount}"
            )
            if c.price_increased:
                line += f"  PRICE UP +{c.pct_change:.0f}%"
            print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
