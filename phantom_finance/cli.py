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
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import budget, categorize, ingest, ledger, llm, networth, presets, recurring, reporter, scenario
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
    p_rep.add_argument("--quarter", help="write a quarterly report instead, e.g. 2026Q2")

    p_sum = sub.add_parser("summary", help="print or write aggregate monthly JSON/text")
    p_sum.add_argument("--month", default=date.today().isoformat()[:7])
    p_sum.add_argument("--currency", default="TWD")
    p_sum.add_argument("--json", action="store_true", help="print stable JSON")
    p_sum.add_argument("--out", type=Path, help="write stable JSON artifact to this path")

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

    p_recat = sub.add_parser(
        "recat",
        help="re-categorize; with MATCH CATEGORY, correct + learn a durable rule",
    )
    p_recat.add_argument("match", nargs="?", help="substring of the description to correct")
    p_recat.add_argument("category", nargs="?", help="category to assign + remember")

    sub.add_parser("recurring", help="list detected recurring charges / subscriptions")
    p_scenario = sub.add_parser(
        "scenario-demo",
        help="write a synthetic subscription/scenario artifact bundle",
    )
    p_scenario.add_argument("--out", type=Path, required=True)
    p_planning = sub.add_parser(
        "planning-scenario",
        help="write a synthetic recurring/net-worth planning scenario bundle",
    )
    p_planning.add_argument("--out", type=Path, required=True)
    p_nw = sub.add_parser(
        "net-worth",
        help="show net worth (assets - liabilities) and spendable cash",
    )
    p_nw.add_argument("--currency", default="TWD")

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
        if getattr(args, "quarter", None):
            out = reporter.write_quarter_report(args.quarter)
        else:
            out = reporter.write_report(args.month)
        print(f"report written: {out}")

    elif args.cmd == "summary":
        payload = reporter.monthly_summary_artifact(
            ledger.load(), args.month, base_currency=args.currency
        )
        if args.out:
            reporter.write_summary_artifact(payload, args.out)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(reporter.render_summary_text(payload))

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
        if args.match and args.category:
            # manual correction: learn a durable rule, then backfill every match
            keyword = categorize.derive_keyword(args.match)
            categorize.add_user_rule(keyword, args.category)
            changed = 0
            for t in txns:
                if keyword in t.description.lower() and t.category != args.category:
                    t.category = args.category
                    changed += 1
            ledger.rewrite(txns)
            print(f"learned rule {keyword!r} -> {args.category}; backfilled {changed} txns")
        elif args.match or args.category:
            print("usage: phantom-finance recat [MATCH CATEGORY]", file=sys.stderr)
            return 2
        else:
            changed = categorize.apply(txns, llm=llm.make_categorizer())
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

    elif args.cmd == "scenario-demo":
        out_dir = scenario.write_scenario_demo_bundle(args.out)
        print(
            json.dumps(
                {"out_dir": str(out_dir), "artifacts": scenario.PUBLIC_ARTIFACTS},
                ensure_ascii=False,
                indent=2,
            )
        )

    elif args.cmd == "planning-scenario":
        out_dir = scenario.write_planning_scenario_bundle(args.out)
        print(
            json.dumps(
                {
                    "out_dir": str(out_dir),
                    "artifacts": scenario.PLANNING_SCENARIO_ARTIFACTS,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    elif args.cmd == "net-worth":
        txns = ledger.load()
        nw = networth.net_worth(txns, base=args.currency)
        cash = networth.cashflow_total(txns, base=args.currency)
        print(f"net worth: {nw} {args.currency}")
        print(f"spendable cash: {cash} {args.currency}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
