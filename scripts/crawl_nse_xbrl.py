from __future__ import annotations

import argparse

from crawler.nse_xbrl.client import NSEClient
from crawler.nse_xbrl.crawler import NSEXBRLCrawler
from crawler.nse_xbrl.storage import XBRLStorage


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Crawl NSE financial-result XBRL files."
        )
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="NSE symbol, e.g. RELIANCE",
    )

    parser.add_argument(
        "--period",
        default="Quarterly",
        choices=[
            "Quarterly",
            "Annual",
        ],
        help="NSE result period.",
    )

    parser.add_argument(
        "--raw-dir",
        default="data/raw/xbrl",
        help="Raw XBRL storage directory.",
    )

    args = parser.parse_args()

    # ========================================================
    # Components
    # ========================================================

    client = NSEClient()

    storage = XBRLStorage(
        root=args.raw_dir
    )

    crawler = NSEXBRLCrawler(
        client=client,
        storage=storage,
    )

    # ========================================================
    # Initialize NSE session
    # ========================================================

    print(
        "[NSE] Initializing session..."
    )

    client.initialize()

    print(
        "[NSE] Session initialized."
    )

    # ========================================================
    # Crawl
    # ========================================================

    filings = crawler.crawl_company(
        symbol=args.symbol,
        period=args.period,
    )

    # ========================================================
    # Summary
    # ========================================================

    downloaded = [
        filing
        for filing in filings
        if filing.local_file
    ]

    print()
    print("=" * 80)
    print("NSE XBRL CRAWL COMPLETE")
    print("=" * 80)

    print(
        f"Symbol       : "
        f"{args.symbol.upper()}"
    )

    print(
        f"Records      : "
        f"{len(filings)}"
    )

    print(
        f"XBRL saved   : "
        f"{len(downloaded)}"
    )

    print(
        f"Storage      : "
        f"{args.raw_dir}"
    )


if __name__ == "__main__":
    main()