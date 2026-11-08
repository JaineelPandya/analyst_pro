from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from market_intelligence.repositories.feed_repository import FeedRepository

app = FastAPI(
    title="Analyst Pro Market Intelligence API",
    version="0.1.0",
    description="Company filings and financial intelligence feed.",
)

repository = FeedRepository()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/feed")
def get_feed(
    symbol: str | None = None,
    category: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    if category:
        category = category.upper()
        allowed = {
            "BUSINESS_UPDATE",
            "CAPEX",
            "FUND_RAISE",
            "FINANCIAL_RESULTS",
            "ORDER_WIN",
            "CORPORATE_ACTION",
            "REGULATORY",
            "SOCIAL_TREND",
            "OTHER",
        }

        if category not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported category: {category}",
            )

    result = repository.list_items(
        symbol=symbol,
        category=category,
        page=page,
        page_size=page_size,
    )

    return {
        **result,
        "items": [
            item.model_dump(mode="json")
            for item in result["items"]
        ],
    }


@app.get("/api/v1/feed/{item_id}")
def get_feed_item(item_id: str):
    item = repository.get_by_id(item_id)

    if item is None:
        raise HTTPException(status_code=404, detail="Feed item not found")

    return item.model_dump(mode="json")