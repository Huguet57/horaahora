from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from backend.domain.models import (
    ActivePushSubscription,
    CastellEvent,
    ChatTurn,
    HourByHourItem,
    NotificationIngestionResult,
    NotificationSendResult,
    ParsedCastellQuery,
    PendingNotificationDelivery,
    PushSubscriptionRegistration,
)


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


class PushSubscriptionRepository(Protocol):
    def register(
        self,
        registration: PushSubscriptionRegistration,
        *,
        environment: str,
        topic: str,
    ) -> None: ...

    def unregister(self, installation_id: str, *, environment: str, topic: str) -> None: ...


class NotificationRepository(PushSubscriptionRepository, Protocol):
    def list_active_subscriptions(self) -> list[ActivePushSubscription]: ...

    def ingest_hour_by_hour(
        self, items: list[HourByHourItem]
    ) -> NotificationIngestionResult: ...

    def claim_deliveries(
        self,
        limit: int,
        *,
        lock_seconds: int = 60,
        now: datetime | None = None,
    ) -> list[PendingNotificationDelivery]: ...

    def mark_delivered(self, delivery_id: str) -> None: ...

    def mark_retry(self, delivery_id: str, *, reason: str, retry_at: datetime) -> None: ...

    def mark_failed(self, delivery_id: str, *, reason: str) -> None: ...

    def mark_invalid_token(
        self, delivery: PendingNotificationDelivery, *, reason: str
    ) -> None: ...

    def cleanup(self, *, now: datetime | None = None) -> dict[str, int]: ...


class NotificationGateway(Protocol):
    def send(self, delivery: PendingNotificationDelivery) -> NotificationSendResult: ...
