from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


EventCategory = Literal[
    "BUSINESS_UPDATE",
    "CAPEX",
    "FUND_RAISE",
    "FINANCIAL_RESULTS",
    "ORDER_WIN",
    "CORPORATE_ACTION",
    "REGULATORY",
    "SOCIAL_TREND",
    "OTHER",
]

SourceType = Literal["OFFICIAL", "NEWS", "SOCIAL"]


class FeedItem(BaseModel):
    id: str

    source: str
    source_record_id: str

    symbol: str | None = None
    company_name: str | None = None

    category: EventCategory = "OTHER"
    headline: str
    summary: str | None = None

    source_url: str | None = None
    source_type: SourceType = "OFFICIAL"

    published_at: datetime | None = None
    collected_at: datetime

    relevance_score: float = Field(default=0.0, ge=0, le=1)
    materiality_score: float = Field(default=0.0, ge=0, le=1)

    classification_method: str = "rules_v1"
    evidence: dict[str, Any] = Field(default_factory=dict)