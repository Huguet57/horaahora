from datetime import datetime
from typing import Protocol

from backend.domain.content.models import HourByHourItem
from backend.domain.notifications.models import (
    ActivePushSubscription,
    NotificationIngestionResult,
    NotificationSendResult,
    PendingNotificationDelivery,
    PushSubscriptionRegistration,
)


class PushSubscriptionRepository(Protocol):
    def register(
        self,
        registration: PushSubscriptionRegistration,
        *,
        environment: str,
        topic: str,
    ) -> None: ...
    def unregister(self, installation_id: str, *, environment: str, topic: str) -> None: ...
    def list_active_subscriptions(self) -> list[ActivePushSubscription]: ...


class NotificationRepository(Protocol):
    def ingest_hour_by_hour(self, items: list[HourByHourItem]) -> NotificationIngestionResult: ...
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
    def mark_invalid_token(self, delivery: PendingNotificationDelivery, *, reason: str) -> None: ...
    def cleanup(self, *, now: datetime | None = None) -> dict[str, int]: ...


class NotificationGateway(Protocol):
    def send(self, delivery: PendingNotificationDelivery) -> NotificationSendResult: ...
