from market_intelligence.repositories.feed_repository import FeedRepository
from market_intelligence.services.normalizer import normalize_nse_filing


def ingest_nse_filings(
    filings: list,
    repository: FeedRepository | None = None,
) -> dict[str, int]:
    repository = repository or FeedRepository()

    items = [
        normalize_nse_filing(filing)
        for filing in filings
    ]

    return repository.upsert_many(items)