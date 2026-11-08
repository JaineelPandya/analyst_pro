from crawler.nse_xbrl.crawler import NSEXBRLCrawler
from market_intelligence.services.ingestion import ingest_nse_filings


def refresh_company(
    symbol: str,
    period: str = "Quarterly",
) -> dict[str, int]:
    crawler = NSEXBRLCrawler()

    filings = crawler.crawl_company(
        symbol=symbol,
        period=period,
    )

    result = ingest_nse_filings(filings)

    return {
        **result,
        "fetched": len(filings),
        "symbol": symbol.upper(),
    }