import pathlib

from mcp.server.fastmcp import FastMCP

from phantom_finance import ledger
from phantom_finance.reporter import monthly_summary_artifact


_PACKAGE_DIR = pathlib.Path(__file__).resolve().parent

mcp = FastMCP("phantom-finance")


@mcp.tool()
def finance_monthly_summary(month: str, currency: str = "TWD") -> dict:
    """Return an aggregate-only monthly finance summary from the local ledger."""
    txns = ledger.load()
    return monthly_summary_artifact(txns, month, base_currency=currency)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
