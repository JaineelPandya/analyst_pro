from __future__ import annotations

import time
import requests


class NSEClient:

    BASE_URL = "https://www.nseindia.com"

    FINANCIAL_RESULTS_ENDPOINT = (
        "/api/corporates-financial-results"
    )

    def __init__(
        self,
        timeout: int = 30,
        retries: int = 3,
        sleep_seconds: float = 1.0,
    ):
        self.timeout = timeout
        self.retries = retries
        self.sleep_seconds = sleep_seconds

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/153.0.0.0 "
                    "Safari/537.36"
                ),
                "Accept": (
                    "application/json,"
                    "text/plain,"
                    "*/*"
                ),
                "Accept-Language": (
                    "en-US,en;q=0.9"
                ),
                "Referer": (
                    "https://www.nseindia.com/"
                    "companies-listing/"
                    "corporate-filings-financial-results"
                ),
                "Connection": "keep-alive",
            }
        )

    def initialize(self) -> None:

        url = (
            self.BASE_URL
            + "/companies-listing/"
            + "corporate-filings-financial-results"
        )

        response = self.session.get(
            url,
            timeout=self.timeout,
        )

        response.raise_for_status()

    def get_financial_results(
        self,
        symbol: str,
        period: str = "Quarterly",
    ) -> list[dict]:

        params = {
            "index": "equities",
            "symbol": symbol.upper(),
            "period": period,
        }

        url = (
            self.BASE_URL
            + self.FINANCIAL_RESULTS_ENDPOINT
        )

        last_error = None

        for attempt in range(
            1,
            self.retries + 1,
        ):

            try:

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                data = response.json()

                if isinstance(data, list):
                    return data

                if isinstance(data, dict):

                    for key in (
                        "data",
                        "results",
                        "records",
                    ):

                        value = data.get(key)

                        if isinstance(value, list):
                            return value

                raise ValueError(
                    "Unexpected NSE response format."
                )

            except Exception as exc:

                last_error = exc

                if attempt < self.retries:
                    time.sleep(
                        self.sleep_seconds * attempt
                    )

        raise RuntimeError(
            "Unable to fetch NSE financial "
            f"results for {symbol}: "
            f"{last_error}"
        )

    def download_xbrl(
        self,
        xbrl_url: str,
    ) -> bytes:

        if not xbrl_url:
            raise ValueError(
                "XBRL URL is empty."
            )

        last_error = None

        for attempt in range(
            1,
            self.retries + 1,
        ):

            try:

                response = self.session.get(
                    xbrl_url,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                content = response.content

                if not content:
                    raise ValueError(
                        "Downloaded XBRL file is empty."
                    )

                return content

            except Exception as exc:

                last_error = exc

                if attempt < self.retries:
                    time.sleep(
                        self.sleep_seconds * attempt
                    )

        raise RuntimeError(
            "Unable to download XBRL: "
            f"{xbrl_url} | {last_error}"
        )