from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from backend.domain.models import CastellEvent, ChatTurn, HourByHourItem, ParsedCastellQuery


class QueryInterpreter(Protocol):
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery: ...


class HourByHourSource(Protocol):
    def fetch(self) -> list[HourByHourItem]: ...


class AgendaSource(Protocol):
    source_id: str

    def fetch_month(self, year: int, month: int) -> list[CastellEvent]: ...


class ContentRepository(Protocol):
    def upsert_hour_by_hour(self, items: list[HourByHourItem]) -> None: ...

    def list_hour_by_hour(self, offset: int, limit: int) -> list[HourByHourItem]: ...

    def count_hour_by_hour(self) -> int: ...

    def latest_hour_by_hour_update(self) -> datetime | None: ...

    def replace_agenda_month(
        self, source_id: str, year: int, month: int, items: list[CastellEvent]
    ) -> None: ...

    def list_agenda(
        self,
        date_from: date,
        date_to: date,
        group: str | None,
        municipality: str | None,
        offset: int,
        limit: int,
    ) -> list[CastellEvent]: ...

    def count_agenda(
        self,
        date_from: date,
        date_to: date,
        group: str | None,
        municipality: str | None,
    ) -> int: ...

    def latest_agenda_month_sync(self, source_id: str, year: int, month: int) -> datetime | None: ...


class RateLimiter(Protocol):
    def allow(self, identifier: str) -> tuple[bool, int]:
        """Return whether the request is accepted and seconds until reset."""
        ...


class NotificationGateway(Protocol):
    def publish_hour_by_hour(self, item: HourByHourItem) -> None: ...
