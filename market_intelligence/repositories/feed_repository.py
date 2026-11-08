import json
import os
import tempfile
from pathlib import Path

from market_intelligence.models import FeedItem


class FeedRepository:
    """
    Small JSONL-backed repository for the MVP.

    Each feed item is stored once by its canonical ID.
    Writes use a temporary file and atomic replacement.
    """

    def __init__(
        self,
        path: str = "data/market_intelligence/feed.jsonl",
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> dict[str, FeedItem]:
        items: dict[str, FeedItem] = {}

        if not self.path.exists():
            return items

        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                try:
                    item = FeedItem.model_validate_json(line)
                    items[item.id] = item
                except Exception as exc:
                    raise ValueError(
                        f"Invalid feed record in {self.path}: {exc}"
                    ) from exc

        return items

    def upsert_many(
        self,
        items: list[FeedItem],
    ) -> dict[str, int]:
        existing = self._read_all()
        inserted = 0
        updated = 0

        for item in items:
            if item.id in existing:
                # Preserve the original collection timestamp when
                # refreshing a record with the same stable identity.
                previous = existing[item.id]
                item = item.model_copy(
                    update={"collected_at": previous.collected_at}
                )
                updated += 1
            else:
                inserted += 1

            existing[item.id] = item

        fd, temp_name = tempfile.mkstemp(
            prefix="feed_",
            suffix=".jsonl",
            dir=str(self.path.parent),
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                for item in existing.values():
                    file.write(item.model_dump_json() + "\n")

            os.replace(temp_name, self.path)

        except Exception:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
            raise

        return {
            "inserted": inserted,
            "updated": updated,
            "total": len(existing),
        }

    def get_by_id(self, item_id: str) -> FeedItem | None:
        """
        Fetch a single feed item by its canonical ID.
        """
        items = self._read_all()
        return items.get(item_id)

    def list_items(
        self,
        *,
        symbol: str | None = None,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        items = list(self._read_all().values())

        if symbol:
            items = [
                item for item in items
                if item.symbol and item.symbol.upper() == symbol.upper()
            ]

        if category:
            items = [
                item for item in items
                if item.category == category.upper()
            ]

        # Unknown timestamps sort after known timestamps.
        items.sort(
            key=lambda item: (
                item.published_at is not None,
                item.published_at.timestamp()
                if item.published_at is not None
                else 0,
                item.id,
            ),
            reverse=True,
        )

        total = len(items)
        start = (page - 1) * page_size

        return {
            "items": items[start:start + page_size],
            "page": page,
            "page_size": page_size,
            "total": total,
        }