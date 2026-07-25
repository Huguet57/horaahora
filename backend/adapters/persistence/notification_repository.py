from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import (
    NotificationDeliveryRecord,
    NotificationOutboxRecord,
    PushSubscriptionRecord,
)
from backend.adapters.persistence.notification_ingestion import ingest_hour_by_hour
from backend.adapters.persistence.notification_support import revoked_token
from backend.adapters.persistence.repository_support import database_datetime, resolve_engine
from backend.domain.content.models import HourByHourItem
from backend.domain.notifications.models import (
    NotificationIngestionResult,
    PendingNotificationDelivery,
)


class SQLAlchemyNotificationRepository:
    def __init__(self, database: Database) -> None:
        self.database, self.engine = resolve_engine(database)

    def ingest_hour_by_hour(self, items: list[HourByHourItem]) -> NotificationIngestionResult:
        return ingest_hour_by_hour(self.engine, items)

    def claim_deliveries(
        self,
        limit: int,
        *,
        lock_seconds: int = 60,
        now: datetime | None = None,
    ) -> list[PendingNotificationDelivery]:
        now = now or datetime.now(UTC)
        database_now = database_datetime(now)
        lock_until = database_datetime(now + timedelta(seconds=lock_seconds))
        with Session(self.engine) as session, session.begin():
            query = (
                select(
                    NotificationDeliveryRecord,
                    NotificationOutboxRecord,
                    PushSubscriptionRecord,
                )
                .join(
                    NotificationOutboxRecord,
                    NotificationOutboxRecord.id == NotificationDeliveryRecord.outbox_id,
                )
                .join(
                    PushSubscriptionRecord,
                    PushSubscriptionRecord.id == NotificationDeliveryRecord.subscription_id,
                )
                .where(
                    NotificationDeliveryRecord.status.in_(("pending", "retry", "processing")),
                    NotificationDeliveryRecord.delivered_at.is_(None),
                    NotificationDeliveryRecord.next_attempt_at <= database_now,
                    or_(
                        NotificationDeliveryRecord.locked_until.is_(None),
                        NotificationDeliveryRecord.locked_until <= database_now,
                    ),
                    PushSubscriptionRecord.hour_by_hour_enabled.is_(True),
                    PushSubscriptionRecord.invalidated_at.is_(None),
                )
                .order_by(NotificationDeliveryRecord.created_at, NotificationDeliveryRecord.id)
                .limit(limit)
            )
            if self.engine.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True, of=NotificationDeliveryRecord)
            result: list[PendingNotificationDelivery] = []
            for delivery, outbox, subscription in session.execute(query).all():
                delivery.status = "processing"
                delivery.locked_until = lock_until
                delivery.attempt_count += 1
                delivery.updated_at = database_now
                result.append(
                    PendingNotificationDelivery(
                        id=delivery.id,
                        subscription_id=subscription.id,
                        outbox_id=outbox.id,
                        device_token=subscription.device_token,
                        environment=subscription.environment,
                        topic=subscription.topic,
                        title=outbox.title,
                        body=outbox.body,
                        url=outbox.url,
                        collapse_id=outbox.collapse_id,
                        attempt_count=delivery.attempt_count,
                    )
                )
            return result

    def mark_delivered(self, delivery_id: str) -> None:
        now = database_datetime(datetime.now(UTC))
        with Session(self.engine) as session, session.begin():
            delivery = session.get(NotificationDeliveryRecord, delivery_id)
            if delivery is not None:
                delivery.status = "delivered"
                delivery.delivered_at = now
                delivery.locked_until = None
                delivery.last_error = ""
                delivery.updated_at = now

    def mark_retry(self, delivery_id: str, *, reason: str, retry_at: datetime) -> None:
        with Session(self.engine) as session, session.begin():
            delivery = session.get(NotificationDeliveryRecord, delivery_id)
            if delivery is not None:
                delivery.status = "retry"
                delivery.next_attempt_at = database_datetime(retry_at)
                delivery.locked_until = None
                delivery.last_error = reason
                delivery.updated_at = database_datetime(datetime.now(UTC))

    def mark_failed(self, delivery_id: str, *, reason: str) -> None:
        with Session(self.engine) as session, session.begin():
            delivery = session.get(NotificationDeliveryRecord, delivery_id)
            if delivery is not None:
                delivery.status = "failed"
                delivery.locked_until = None
                delivery.last_error = reason
                delivery.updated_at = database_datetime(datetime.now(UTC))

    def mark_invalid_token(self, delivery: PendingNotificationDelivery, *, reason: str) -> None:
        now = database_datetime(datetime.now(UTC))
        with Session(self.engine) as session, session.begin():
            subscription = session.get(PushSubscriptionRecord, delivery.subscription_id)
            if subscription is not None:
                subscription.hour_by_hour_enabled = False
                subscription.invalidated_at = now
                subscription.updated_at = now
                subscription.device_token = revoked_token(subscription.id)
            session.execute(
                update(NotificationDeliveryRecord)
                .where(
                    NotificationDeliveryRecord.subscription_id == delivery.subscription_id,
                    NotificationDeliveryRecord.delivered_at.is_(None),
                )
                .values(status="failed", locked_until=None, last_error=reason, updated_at=now)
            )

    def cleanup(self, *, now: datetime | None = None) -> dict[str, int]:
        now = now or datetime.now(UTC)
        delivery_cutoff = database_datetime(now - timedelta(days=30))
        subscription_cutoff = database_datetime(now - timedelta(days=180))
        database_now = database_datetime(now)
        with Session(self.engine) as session, session.begin():
            stale_records = session.scalars(
                select(PushSubscriptionRecord).where(
                    PushSubscriptionRecord.last_seen_at < subscription_cutoff,
                    PushSubscriptionRecord.invalidated_at.is_(None),
                )
            ).all()
            for subscription in stale_records:
                subscription.hour_by_hour_enabled = False
                subscription.invalidated_at = database_now
                subscription.updated_at = database_now
                subscription.device_token = revoked_token(subscription.id)
            deliveries = session.execute(
                delete(NotificationDeliveryRecord).where(
                    NotificationDeliveryRecord.created_at < delivery_cutoff
                )
            ).rowcount
        return {
            "subscriptions_invalidated": len(stale_records),
            "deliveries_deleted": deliveries or 0,
            "outboxes_deleted": 0,
        }
