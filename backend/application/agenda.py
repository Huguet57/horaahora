from dataclasses import dataclass
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from backend.application.pagination import decode_cursor, encode_cursor
from backend.domain.content.models import CastellEvent
from backend.domain.content.ports import AgendaRepository, AgendaSource


@dataclass(frozen=True, slots=True)
class AgendaPage:
    items: list[CastellEvent]
    next_cursor: str | None
    from_cache: bool
    source_status: str


class AgendaService:
    def __init__(
        self,
        repository: AgendaRepository,
        source: AgendaSource | None,
        refresh_seconds: int = 1_800,
        refresh_on_request: bool = True,
    ) -> None:
        self.repository = repository
        self.source = source
        self.refresh_seconds = refresh_seconds
        self.refresh_on_request = refresh_on_request

    def list(
        self,
        date_from: date | None,
        date_to: date | None,
        group: str | None,
        municipality: str | None,
        cursor: str | None,
        limit: int,
        force_refresh: bool = False,
    ) -> AgendaPage:
        today = datetime.now(ZoneInfo("Europe/Madrid")).date()
        date_from = date_from or today
        date_to = date_to or date_from
        if date_to < date_from:
            raise ValueError("La data 'to' no pot ser anterior a 'from'")
        if (date_to - date_from).days > 366:
            raise ValueError("El rang de l'agenda no pot superar un any")

        refreshed = False
        if self.source is not None and self.refresh_on_request:
            for year, month in months_between(date_from, date_to):
                if force_refresh or self._month_is_stale(year, month):
                    try:
                        items = self.source.fetch_month(year, month)
                        self.repository.replace_agenda_month(
                            self.source.source_id, year, month, items
                        )
                        refreshed = True
                    except Exception:
                        if (
                            self.repository.count_agenda(date_from, date_to, group, municipality)
                            == 0
                        ):
                            raise

        offset = decode_cursor(cursor)
        count = self.repository.count_agenda(date_from, date_to, group, municipality)
        items = self.repository.list_agenda(date_from, date_to, group, municipality, offset, limit)
        next_offset = offset + len(items)
        return AgendaPage(
            items=items,
            next_cursor=encode_cursor(next_offset) if next_offset < count else None,
            from_cache=not refreshed,
            source_status="active" if self.source is not None else "unavailable",
        )

    def _month_is_stale(self, year: int, month: int) -> bool:
        if self.source is None:
            return False
        latest = self.repository.latest_agenda_month_sync(self.source.source_id, year, month)
        if latest is None:
            return True
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=UTC)
        return (datetime.now(UTC) - latest).total_seconds() >= self.refresh_seconds


def months_between(date_from: date, date_to: date) -> list[tuple[int, int]]:
    cursor = date(date_from.year, date_from.month, 1)
    months: list[tuple[int, int]] = []
    while cursor <= date_to:
        months.append((cursor.year, cursor.month))
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )
    return months
