from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from backend.domain.models import CalculationResult, CastellEvent, ChatTurn, HourByHourItem
from backend.domain.ports import AgendaSource, ContentRepository, HourByHourSource, QueryInterpreter
from backend.domain.scoring import ScoringEngine


@dataclass(frozen=True, slots=True)
class HourByHourPage:
    items: list[HourByHourItem]
    next_cursor: str | None
    from_cache: bool


class HourByHourService:
    def __init__(
        self,
        repository: ContentRepository,
        source: HourByHourSource | None,
        refresh_seconds: int = 300,
    ) -> None:
        self.repository = repository
        self.source = source
        self.refresh_seconds = refresh_seconds

    def list(self, cursor: str | None, limit: int, force_refresh: bool = False) -> HourByHourPage:
        refreshed = False
        if self.source is not None and (force_refresh or self._is_stale()):
            try:
                items = self.source.fetch()
                self.repository.upsert_hour_by_hour(items)
                refreshed = True
            except Exception:
                if self.repository.count_hour_by_hour() == 0:
                    raise

        offset = decode_cursor(cursor)
        items = self.repository.list_hour_by_hour(offset, limit)
        next_offset = offset + len(items)
        next_cursor = encode_cursor(next_offset) if next_offset < self.repository.count_hour_by_hour() else None
        return HourByHourPage(items=items, next_cursor=next_cursor, from_cache=not refreshed)

    def _is_stale(self) -> bool:
        latest = self.repository.latest_hour_by_hour_update()
        if latest is None:
            return True
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=UTC)
        return (datetime.now(UTC) - latest).total_seconds() >= self.refresh_seconds


@dataclass(frozen=True, slots=True)
class AgendaPage:
    items: list[CastellEvent]
    next_cursor: str | None
    from_cache: bool
    source_status: str


class AgendaService:
    def __init__(
        self,
        repository: ContentRepository,
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
            for year, month in _months_between(date_from, date_to):
                if force_refresh or self._month_is_stale(year, month):
                    try:
                        items = self.source.fetch_month(year, month)
                        self.repository.replace_agenda_month(
                            self.source.source_id, year, month, items
                        )
                        refreshed = True
                    except Exception:
                        if self.repository.count_agenda(
                            date_from, date_to, group, municipality
                        ) == 0:
                            raise

        offset = decode_cursor(cursor)
        count = self.repository.count_agenda(date_from, date_to, group, municipality)
        items = self.repository.list_agenda(
            date_from, date_to, group, municipality, offset, limit
        )
        next_offset = offset + len(items)
        next_cursor = encode_cursor(next_offset) if next_offset < count else None
        return AgendaPage(
            items=items,
            next_cursor=next_cursor,
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


@dataclass(frozen=True, slots=True)
class AgendaSyncFailure:
    year_month: tuple[int, int]
    error: str


@dataclass(frozen=True, slots=True)
class AgendaSyncResult:
    succeeded: list[tuple[int, int]]
    failed: list[AgendaSyncFailure]


class AgendaSyncService:
    """Prefetch complete months and atomically publish them to the read database."""

    def __init__(self, repository: ContentRepository, source: AgendaSource) -> None:
        self.repository = repository
        self.source = source

    def sync(self, date_from: date, date_to: date) -> AgendaSyncResult:
        if date_to < date_from:
            raise ValueError("La data final no pot ser anterior a la inicial")

        succeeded: list[tuple[int, int]] = []
        failed: list[AgendaSyncFailure] = []
        for year, month in _months_between(date_from, date_to):
            try:
                items = self.source.fetch_month(year, month)
                self.repository.replace_agenda_month(self.source.source_id, year, month, items)
                succeeded.append((year, month))
            except Exception as error:
                failed.append(AgendaSyncFailure((year, month), str(error)))
        return AgendaSyncResult(succeeded=succeeded, failed=failed)


class ChatService:
    def __init__(self, interpreter: QueryInterpreter, scoring_engine: ScoringEngine) -> None:
        self.interpreter = interpreter
        self.scoring_engine = scoring_engine

    async def respond(self, history: list[ChatTurn]) -> CalculationResult:
        if not history or history[-1].role != "user":
            raise ValueError("L'últim missatge ha de ser de l'usuari")
        current = history[-1]
        query = await self.interpreter.interpret(history[:-1], current.content)
        return self.scoring_engine.calculate(query)


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode("ascii")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        value = int(base64.urlsafe_b64decode(padded).decode("ascii"))
        return max(0, value)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Cursor no vàlid") from None


def _months_between(date_from: date, date_to: date) -> list[tuple[int, int]]:
    cursor = date(date_from.year, date_from.month, 1)
    months: list[tuple[int, int]] = []
    while cursor <= date_to:
        months.append((cursor.year, cursor.month))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return months
