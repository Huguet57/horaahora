from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.domain.models import NotificationDisposition
from backend.domain.ports import HourByHourSource, NotificationGateway, NotificationRepository


@dataclass(frozen=True, slots=True)
class NotificationRunResult:
    status: str
    notifications_created: int = 0
    attempted: int = 0
    delivered: int = 0
    retried: int = 0
    invalidated: int = 0
    failed: int = 0


class HourByHourNotificationCoordinator:
    lock_key = 2_026_072_201

    def __init__(
        self,
        repository: NotificationRepository,
        source: HourByHourSource,
        gateway: NotificationGateway,
        *,
        enabled: bool,
        batch_size: int = 250,
        time_budget_seconds: float = 45,
    ) -> None:
        self.repository = repository
        self.source = source
        self.gateway = gateway
        self.enabled = enabled
        self.batch_size = batch_size
        self.time_budget_seconds = time_budget_seconds

    def run(self) -> NotificationRunResult:
        if not self.enabled:
            return NotificationRunResult(status="disabled")

        started = time.monotonic()
        database = getattr(self.repository, "database", None)
        lock = database.advisory_lock(self.lock_key) if database is not None else _AlwaysLocked()
        with lock as acquired:
            if not acquired:
                return NotificationRunResult(status="already_running")
            ingestion = self.repository.ingest_hour_by_hour(self.source.fetch())
            attempted = delivered = retried = invalidated = failed = 0
            deliveries = self.repository.claim_deliveries(limit=self.batch_size)
            for delivery in deliveries:
                if time.monotonic() - started >= self.time_budget_seconds:
                    self.repository.mark_retry(
                        delivery.id,
                        reason="TimeBudgetExceeded",
                        retry_at=datetime.now(UTC) + timedelta(minutes=1),
                    )
                    retried += 1
                    continue
                attempted += 1
                try:
                    result = self.gateway.send(delivery)
                except Exception as error:
                    self.repository.mark_retry(
                        delivery.id,
                        reason=type(error).__name__,
                        retry_at=_retry_at(delivery.attempt_count),
                    )
                    retried += 1
                    continue
                if result.disposition is NotificationDisposition.DELIVERED:
                    self.repository.mark_delivered(delivery.id)
                    delivered += 1
                elif result.disposition is NotificationDisposition.RETRY:
                    self.repository.mark_retry(
                        delivery.id,
                        reason=result.reason,
                        retry_at=_retry_at(delivery.attempt_count),
                    )
                    retried += 1
                elif result.disposition is NotificationDisposition.INVALID_TOKEN:
                    self.repository.mark_invalid_token(delivery, reason=result.reason)
                    invalidated += 1
                else:
                    self.repository.mark_failed(delivery.id, reason=result.reason)
                    failed += 1
            return NotificationRunResult(
                status="completed",
                notifications_created=ingestion.notifications_created,
                attempted=attempted,
                delivered=delivered,
                retried=retried,
                invalidated=invalidated,
                failed=failed,
            )


class _AlwaysLocked:
    def __enter__(self) -> bool:
        return True

    def __exit__(self, *_args) -> None:
        return None


def _retry_at(attempt_count: int) -> datetime:
    delay = min(3_600, 30 * (2 ** min(attempt_count, 7)))
    return datetime.now(UTC) + timedelta(seconds=delay)
