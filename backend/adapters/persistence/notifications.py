from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.sqlalchemy import (
    HourByHourRecord,
    NotificationDeliveryRecord,
    NotificationOutboxRecord,
    NotificationSyncStateRecord,
    PushSubscriptionRecord,
)
from backend.domain.models import (
    ActivePushSubscription,
    HourByHourItem,
    NotificationIngestionResult,
    PendingNotificationDelivery,
    PushSubscriptionRegistration,
)


class SQLAlchemyNotificationRepository:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.engine = database.engine

    def register(
        self,
        registration: PushSubscriptionRegistration,
        *,
        environment: str,
        topic: str,
    ) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as session, session.begin():
            collision = session.scalar(
                select(PushSubscriptionRecord).where(
                    PushSubscriptionRecord.device_token == registration.device_token,
                    PushSubscriptionRecord.environment == environment,
                    PushSubscriptionRecord.topic == topic,
                    PushSubscriptionRecord.installation_id != registration.installation_id,
                )
            )
            if collision is not None:
                collision.hour_by_hour_enabled = False
                collision.invalidated_at = now
                collision.updated_at = now
                collision.device_token = _revoked_token(collision.id)

            record = session.scalar(
                select(PushSubscriptionRecord).where(
                    PushSubscriptionRecord.installation_id == registration.installation_id,
                    PushSubscriptionRecord.environment == environment,
                    PushSubscriptionRecord.topic == topic,
                )
            )
            if record is None:
                record = PushSubscriptionRecord(
                    id=str(uuid4()),
                    installation_id=registration.installation_id,
                    environment=environment,
                    topic=topic,
                    created_at=now,
                )
                session.add(record)
            record.device_token = registration.device_token
            record.hour_by_hour_enabled = True
            record.app_version = registration.app_version
            record.locale = registration.locale
            record.updated_at = now
            record.last_seen_at = now
            record.invalidated_at = None

    def unregister(self, installation_id: str, *, environment: str, topic: str) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as session, session.begin():
            record = session.scalar(
                select(PushSubscriptionRecord).where(
                    PushSubscriptionRecord.installation_id == installation_id,
                    PushSubscriptionRecord.environment == environment,
                    PushSubscriptionRecord.topic == topic,
                )
            )
            if record is not None:
                record.hour_by_hour_enabled = False
                record.invalidated_at = now
                record.updated_at = now
                record.device_token = _revoked_token(record.id)

    def list_active_subscriptions(self) -> list[ActivePushSubscription]:
        with Session(self.engine) as session:
            records = session.scalars(
                select(PushSubscriptionRecord).where(
                    PushSubscriptionRecord.hour_by_hour_enabled.is_(True),
                    PushSubscriptionRecord.invalidated_at.is_(None),
                )
            ).all()
            return [
                ActivePushSubscription(
                    id=record.id,
                    installation_id=record.installation_id,
                    device_token=record.device_token,
                    environment=record.environment,
                    topic=record.topic,
                )
                for record in records
            ]

    def ingest_hour_by_hour(
        self, items: list[HourByHourItem]
    ) -> NotificationIngestionResult:
        now = datetime.now(UTC)
        baseline_created = False
        notifications_created = 0
        with Session(self.engine) as session, session.begin():
            active_subscriptions = session.scalars(
                select(PushSubscriptionRecord).where(
                    PushSubscriptionRecord.hour_by_hour_enabled.is_(True),
                    PushSubscriptionRecord.invalidated_at.is_(None),
                )
            ).all()
            states: dict[str, NotificationSyncStateRecord | None] = {}
            for item in items:
                if item.source_id not in states:
                    states[item.source_id] = session.get(
                        NotificationSyncStateRecord, item.source_id
                    )
                record = session.scalar(
                    select(HourByHourRecord).where(
                        HourByHourRecord.source_id == item.source_id,
                        HourByHourRecord.external_id == item.external_id,
                    )
                )
                if record is None:
                    record = HourByHourRecord(
                        id=item.id,
                        source_id=item.source_id,
                        external_id=item.external_id,
                        created_at=_database_datetime(item.created_at),
                    )
                    session.add(record)
                _update_hour_by_hour_record(record, item)

            items_by_source: dict[str, list[HourByHourItem]] = {}
            for item in items:
                items_by_source.setdefault(item.source_id, []).append(item)

            for source_id, state in states.items():
                content_hash = _content_hash(items_by_source[source_id])
                if state is None:
                    state = NotificationSyncStateRecord(
                        source_id=source_id,
                        initialized_at=now,
                        last_synced_at=now,
                        last_content_hash=content_hash,
                    )
                    session.add(state)
                    baseline_created = True
                else:
                    state.last_synced_at = now
                    state.last_content_hash = content_hash

            baseline_sources = {
                source_id for source_id, state in states.items() if state is None
            }
            for item in items:
                existing_outbox = session.scalar(
                    select(NotificationOutboxRecord.id).where(
                        NotificationOutboxRecord.event_type == "hour_by_hour",
                        NotificationOutboxRecord.source_id == item.source_id,
                        NotificationOutboxRecord.external_id == item.external_id,
                    )
                )
                if existing_outbox is not None:
                    continue
                outbox = NotificationOutboxRecord(
                    id=str(uuid4()),
                    event_type="hour_by_hour",
                    source_id=item.source_id,
                    external_id=item.external_id,
                    title=item.display_title or item.title,
                    body=item.summary or item.title,
                    url=item.action_url or item.article_url,
                    collapse_id=_collapse_id(item.external_id),
                    created_at=now,
                )
                session.add(outbox)
                # Baseline rows are durable deduplication markers. They intentionally
                # have no delivery targets, so installing the new backend can never
                # emit every historical item on its second synchronization.
                if item.source_id in baseline_sources:
                    continue
                notifications_created += 1
                # The models intentionally avoid ORM relationships; make the
                # foreign-key parent visible before inserting delivery rows.
                session.flush()
                for subscription in active_subscriptions:
                    session.add(
                        NotificationDeliveryRecord(
                            id=str(uuid4()),
                            outbox_id=outbox.id,
                            subscription_id=subscription.id,
                            status="pending",
                            attempt_count=0,
                            next_attempt_at=now,
                            locked_until=None,
                            delivered_at=None,
                            last_error="",
                            created_at=now,
                            updated_at=now,
                        )
                    )

        return NotificationIngestionResult(
            baseline_created=baseline_created,
            notifications_created=notifications_created,
        )

    def claim_deliveries(
        self,
        limit: int,
        *,
        lock_seconds: int = 60,
        now: datetime | None = None,
    ) -> list[PendingNotificationDelivery]:
        now = now or datetime.now(UTC)
        database_now = _database_datetime(now)
        lock_until = _database_datetime(now + timedelta(seconds=lock_seconds))
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
            rows = session.execute(query).all()
            result: list[PendingNotificationDelivery] = []
            for delivery, outbox, subscription in rows:
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
        now = _database_datetime(datetime.now(UTC))
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
                delivery.next_attempt_at = _database_datetime(retry_at)
                delivery.locked_until = None
                delivery.last_error = reason
                delivery.updated_at = _database_datetime(datetime.now(UTC))

    def mark_failed(self, delivery_id: str, *, reason: str) -> None:
        with Session(self.engine) as session, session.begin():
            delivery = session.get(NotificationDeliveryRecord, delivery_id)
            if delivery is not None:
                delivery.status = "failed"
                delivery.locked_until = None
                delivery.last_error = reason
                delivery.updated_at = _database_datetime(datetime.now(UTC))

    def mark_invalid_token(
        self, delivery: PendingNotificationDelivery, *, reason: str
    ) -> None:
        now = _database_datetime(datetime.now(UTC))
        with Session(self.engine) as session, session.begin():
            subscription = session.get(PushSubscriptionRecord, delivery.subscription_id)
            if subscription is not None:
                subscription.hour_by_hour_enabled = False
                subscription.invalidated_at = now
                subscription.updated_at = now
                subscription.device_token = _revoked_token(subscription.id)
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
        delivery_cutoff = _database_datetime(now - timedelta(days=30))
        subscription_cutoff = _database_datetime(now - timedelta(days=180))
        database_now = _database_datetime(now)
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
                subscription.device_token = _revoked_token(subscription.id)
            deliveries = session.execute(
                delete(NotificationDeliveryRecord).where(
                    NotificationDeliveryRecord.created_at < delivery_cutoff
                )
            ).rowcount
        return {
            "subscriptions_invalidated": len(stale_records),
            "deliveries_deleted": deliveries or 0,
            # Outbox rows also form the permanent event deduplication ledger.
            "outboxes_deleted": 0,
        }


def _update_hour_by_hour_record(record: HourByHourRecord, item: HourByHourItem) -> None:
    record.title = item.title
    record.display_title = item.display_title
    record.summary = item.summary
    record.published_at = _database_datetime(item.published_at) if item.published_at else None
    record.source_order = item.source_order
    record.article_url = item.article_url
    record.action_url = item.action_url or ""
    record.attribution = item.attribution
    record.updated_at = _database_datetime(item.updated_at)


def _database_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _collapse_id(external_id: str) -> str:
    value = f"hour-by-hour:{external_id}"
    if len(value.encode("utf-8")) <= 64:
        return value
    return f"hour-by-hour:{hashlib.sha256(external_id.encode()).hexdigest()[:40]}"


def _content_hash(items: list[HourByHourItem]) -> str:
    identifiers = "\n".join(sorted(item.external_id for item in items))
    return hashlib.sha256(identifiers.encode("utf-8")).hexdigest()


def _revoked_token(subscription_id: str) -> str:
    return f"revoked:{subscription_id}"
