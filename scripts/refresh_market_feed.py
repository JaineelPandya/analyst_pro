import argparse
import json

from market_intelligence.providers.nse_xbrl import refresh_company


def main():
    parser = argparse.ArgumentParser(
        description="Fetch NSE XBRL filings and ingest them into the feed."
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="NSE company symbol, e.g. RELIANCE",
    )
    parser.add_argument(
        "--period",
        default="Quarterly",
        help="Period argument supported by the existing NSE client",
    )
    args = parser.parse_args()

    result = refresh_company(
        symbol=args.symbol,
        period=args.period,
    )

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
    