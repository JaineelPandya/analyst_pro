from __future__ import annotations

from typing import Optional

from .client import NSEClient
from .models import NSEFiling
from .storage import XBRLStorage


class NSEXBRLCrawler:

    def __init__(
        self,
        client: Optional[NSEClient] = None,
        storage: Optional[XBRLStorage] = None,
    ):

        self.client = (
            client or NSEClient()
        )

        self.storage = (
            storage
            or XBRLStorage(
                "data/raw/xbrl"
            )
        )

    @staticmethod
    def _first(
        record: dict,
        *keys: str,
    ):

        for key in keys:

            value = record.get(key)

            if value is not None:
                return value

        return None

    def normalize_record(
        self,
        record: dict,
    ) -> NSEFiling:

        symbol = self._first(
            record,
            "symbol",
            "Symbol",
        )

        company_name = self._first(
            record,
            "companyName",
            "company_name",
            "Company Name",
            "companyname",
        )

        xbrl_url = self._first(
            record,
            "xbrl",
            "xbrlUrl",
            "xbrl_url",
            "XBRL",
        )

        filing_date = self._first(
            record,
            "filingDate",
            "filing_date",
        )

        broadcast_datetime = self._first(
            record,
            "broadCastDate",
            "broadcastDate",
            "broadcast_datetime",
            "broadcastDateTime",
        )

        period_ended = self._first(
            record,
            "periodEnded",
            "period_ended",
            "toDate",
        )

        return NSEFiling(
            symbol=symbol or "UNKNOWN",
            company_name=company_name or "",
            period=self._first(
                record,
                "period",
            ),
            period_ended=period_ended,
            relating_to=self._first(
                record,
                "relatingTo",
                "relating_to",
            ),
            financial_year=self._first(
                record,
                "financialYear",
                "financial_year",
            ),
            audited=self._first(
                record,
                "audited",
            ),
            cumulative=self._first(
                record,
                "cumulative",
            ),
            consolidated=self._first(
                record,
                "consolidated",
            ),
            ind_as=self._first(
                record,
                "indAs",
                "ind_as",
            ),
            filing_date=filing_date,
            broadcast_datetime=broadcast_datetime,
            xbrl_url=xbrl_url,
            raw=record,
        )

    def crawl_company(
        self,
        symbol: str,
        period: str = "Quarterly",
    ) -> list[NSEFiling]:

        print()
        print(
            f"[NSE] Fetching "
            f"{symbol.upper()} "
            f"({period})"
        )

        records = (
            self.client.get_financial_results(
                symbol=symbol,
                period=period,
            )
        )

        print(
            f"[NSE] Records found: "
            f"{len(records)}"
        )

        filings = []

        for index, record in enumerate(
            records,
            start=1,
        ):

            filing = (
                self.normalize_record(record)
            )

            print(
                f"[{index}/{len(records)}] "
                f"{filing.symbol} | "
                f"{filing.period_ended} | "
                f"{filing.broadcast_datetime}"
            )

            if not filing.xbrl_url:

                print(
                    "    -> XBRL unavailable"
                )

                filings.append(filing)

                continue

            try:

                content = (
                    self.client.download_xbrl(
                        filing.xbrl_url
                    )
                )

                local_path = (
                    self.storage.save_xbrl(
                        symbol=filing.symbol,
                        content=content,
                        filing_date=(
                            filing.filing_date
                        ),
                        broadcast_datetime=(
                            filing.broadcast_datetime
                        ),
                        xbrl_url=filing.xbrl_url,
                    )
                )

                filing.local_file = str(
                    local_path
                )

                print(
                    "    -> Saved: "
                    f"{local_path}"
                )

                metadata = filing.to_dict()

                self.storage.save_metadata(
                    symbol=filing.symbol,
                    metadata=metadata,
                )

            except Exception as exc:

                print(
                    "    -> DOWNLOAD ERROR: "
                    f"{exc}"
                )

            filings.append(filing)

        return filings