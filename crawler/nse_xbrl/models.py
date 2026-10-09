from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class NSEFiling:

    symbol: str
    company_name: str

    period: Optional[str] = None
    period_ended: Optional[str] = None
    relating_to: Optional[str] = None

    financial_year: Optional[str] = None

    audited: Optional[str] = None
    cumulative: Optional[str] = None
    consolidated: Optional[str] = None
    ind_as: Optional[str] = None

    filing_date: Optional[str] = None
    broadcast_datetime: Optional[str] = None

    xbrl_url: Optional[str] = None

    local_file: Optional[str] = None

    raw: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)