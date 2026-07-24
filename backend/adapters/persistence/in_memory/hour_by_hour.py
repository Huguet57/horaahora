from datetime import datetime
from threading import Lock

from backend.domain.content.models import HourByHourItem


class InMemoryHourByHourRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], HourByHourItem] = {}
        self._lock = Lock()

    def upsert_hour_by_hour(self, items: list[HourByHourItem]) -> None:
        with self._lock:
            for item in items:
                self._items[(item.source_id, item.external_id)] = item

    def list_hour_by_hour(self, offset: int, limit: int) -> list[HourByHourItem]:
        with self._lock:
            ordered = sorted(
                self._items.values(),
                key=lambda item: (
                    item.published_at is not None,
                    item.published_at or item.updated_at,
                    -item.source_order,
                ),
                reverse=True,
            )
            return ordered[offset : offset + limit]

    def count_hour_by_hour(self) -> int:
        with self._lock:
            return len(self._items)

    def latest_hour_by_hour_update(self) -> datetime | None:
        with self._lock:
            return max((item.updated_at for item in self._items.values()), default=None)
