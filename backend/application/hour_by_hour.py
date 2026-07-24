from dataclasses import dataclass
from datetime import UTC, datetime

from backend.application.pagination import decode_cursor, encode_cursor
from backend.domain.content.models import HourByHourItem
from backend.domain.content.ports import HourByHourRepository, HourByHourSource


@dataclass(frozen=True, slots=True)
class HourByHourPage:
    items: list[HourByHourItem]
    next_cursor: str | None
    from_cache: bool


class HourByHourService:
    def __init__(
        self,
        repository: HourByHourRepository,
        source: HourByHourSource | None,
        refresh_seconds: int = 300,
    ) -> None:
        self.repository = repository
        self.source = source
        self.refresh_seconds = refresh_seconds

    def list(
        self, cursor: str | None, limit: int, force_refresh: bool = False
    ) -> HourByHourPage:
        refreshed = False
        if self.source is not None and (force_refresh or self._is_stale()):
            try:
                self.repository.upsert_hour_by_hour(self.source.fetch())
                refreshed = True
            except Exception:
                if self.repository.count_hour_by_hour() == 0:
                    raise

        offset = decode_cursor(cursor)
        items = self.repository.list_hour_by_hour(offset, limit)
        next_offset = offset + len(items)
        next_cursor = (
            encode_cursor(next_offset)
            if next_offset < self.repository.count_hour_by_hour()
            else None
        )
        return HourByHourPage(items=items, next_cursor=next_cursor, from_cache=not refreshed)

    def _is_stale(self) -> bool:
        latest = self.repository.latest_hour_by_hour_update()
        if latest is None:
            return True
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=UTC)
        return (datetime.now(UTC) - latest).total_seconds() >= self.refresh_seconds
