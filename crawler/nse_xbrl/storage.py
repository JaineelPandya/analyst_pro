from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Optional


class XBRLStorage:

    def __init__(
        self,
        root: str = "data/raw/xbrl",
    ):
        self.root = Path(root)

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def symbol_directory(
        self,
        symbol: str,
    ) -> Path:

        directory = (
            self.root / symbol.upper()
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    @staticmethod
    def _safe(value: str) -> str:

        value = value.strip()

        value = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            value,
        )

        return value

    def build_filename(
        self,
        symbol: str,
        filing_date: Optional[str],
        broadcast_datetime: Optional[str],
        xbrl_url: Optional[str],
    ) -> str:

        date_part = (
            broadcast_datetime
            or filing_date
            or "unknown_date"
        )

        date_part = self._safe(
            date_part
        )

        date_part = date_part.replace(
            " ",
            "_",
        )

        date_part = date_part.replace(
            ":",
            "",
        )

        extension = ".xml"

        if xbrl_url:

            lower_url = xbrl_url.lower()

            if ".zip" in lower_url:
                extension = ".zip"

            elif ".xml" in lower_url:
                extension = ".xml"

        url_hash = ""

        if xbrl_url:

            digest = hashlib.sha1(
                xbrl_url.encode("utf-8")
            ).hexdigest()[:8]

            url_hash = f"_{digest}"

        return (
            f"{date_part}"
            f"{url_hash}"
            f"{extension}"
        )

    def save_xbrl(
        self,
        symbol: str,
        content: bytes,
        filing_date: Optional[str],
        broadcast_datetime: Optional[str],
        xbrl_url: Optional[str],
    ) -> Path:

        directory = self.symbol_directory(
            symbol
        )

        filename = self.build_filename(
            symbol=symbol,
            filing_date=filing_date,
            broadcast_datetime=broadcast_datetime,
            xbrl_url=xbrl_url,
        )

        path = directory / filename

        if path.exists():
            return path

        path.write_bytes(content)

        return path

    def save_metadata(
        self,
        symbol: str,
        metadata: dict,
    ) -> Path:

        directory = self.symbol_directory(
            symbol
        )

        path = (
            directory / "manifest.jsonl"
        )

        with path.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    metadata,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

        return path