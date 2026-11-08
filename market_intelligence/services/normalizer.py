import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from dateutil import parser as date_parser

from market_intelligence.models import FeedItem


def _stable_id(source: str, source_record_id: str) -> str:
    raw = f"{source}:{source_record_id}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"feed_{digest}"


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None

    # Handle common ISO timestamps and trailing Z.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text)
    except (TypeError, ValueError):
        pass

    try:
        dt = date_parser.parse(text)
        return dt
    except (TypeError, ValueError, OverflowError):
        return None


def normalize_nse_filing(filing: Any) -> FeedItem:
    """
    Convert an NSEFiling dataclass or its dictionary representation
    into a canonical feed item.

    This creates a financial-results feed record. It does not claim
    that the record is a new corporate announcement.
    """
    if hasattr(filing, "to_dict"):
        record = filing.to_dict()
    elif isinstance(filing, dict):
        record = filing
    else:
        raise TypeError(
            "filing must be an NSEFiling or a dictionary"
        )

    raw = record.get("raw") or {}

    xbrl_url = (
        record.get("xbrl_url")
        or raw.get("xbrl")
        or raw.get("xbrlUrl")
        or raw.get("xbrl_url")
    )

    # Prefer the source URL as a stable filing identifier.
    # Fall back to a canonical hash of the raw record.
    if xbrl_url:
        source_record_id = str(xbrl_url)
    else:
        canonical = json.dumps(
            raw or record,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )
        source_record_id = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    symbol = record.get("symbol")
    company_name = record.get("company_name")

    period_ended = record.get("period_ended")
    financial_year = record.get("financial_year")
    period = record.get("period")

    details = [
        str(value)
        for value in (period, period_ended, financial_year)
        if value
    ]

    headline = (
        f"{company_name or symbol or 'Company'} "
        f"financial results"
    )
    if details:
        headline += f" — {' | '.join(details)}"

    return FeedItem(
        id=_stable_id("NSE_XBRL", source_record_id),
        source="NSE_XBRL",
        source_record_id=source_record_id,
        symbol=str(symbol).upper() if symbol else None,
        company_name=company_name or None,
        category="FINANCIAL_RESULTS",
        headline=headline,
        summary="Financial filing discovered by the NSE XBRL crawler.",
        source_url=str(xbrl_url) if xbrl_url else None,
        source_type="OFFICIAL",
        published_at=_parse_datetime(
            record.get("broadcast_datetime")
            or record.get("filing_date")
        ),
        collected_at=datetime.now(timezone.utc),
        evidence={
            "period": period,
            "period_ended": period_ended,
            "financial_year": financial_year,
            "audited": record.get("audited"),
            "cumulative": record.get("cumulative"),
            "consolidated": record.get("consolidated"),
            "ind_as": record.get("ind_as"),
            "local_file": record.get("local_file"),
            "timestamp_source": (
                "broadcast_datetime"
                if record.get("broadcast_datetime")
                else (
                    "filing_date"
                    if record.get("filing_date")
                    else None
                )
            ),
        },
    )