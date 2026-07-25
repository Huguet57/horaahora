from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.adapters.persistence.hour_by_hour_repository import update_hour_by_hour_record
from backend.adapters.persistence.models import (
    HourByHourRecord,
    NotificationDeliveryRecord,
    NotificationOutboxRecord,
    NotificationSyncStateRecord,
    PushSubscriptionRecord,
)
from backend.adapters.persistence.notification_support import collapse_id, content_hash
from backend.adapters.persistence.repository_support import database_datetime
from backend.domain.content.models import HourByHourItem
from backend.domain.notifications.models import NotificationIngestionResult


def ingest_hour_by_hour(engine: Engine, items: list[HourByHourItem]) -> NotificationIngestionResult:
    now = datetime.now(UTC)
    baseline_created = False
    notifications_created = 0
    with Session(engine) as session, session.begin():
        active_subscriptions = session.scalars(
            select(PushSubscriptionRecord).where(
                PushSubscriptionRecord.hour_by_hour_enabled.is_(True),
                PushSubscriptionRecord.invalidated_at.is_(None),
            )
        ).all()
        states: dict[str, NotificationSyncStateRecord | None] = {}
        for item in items:
            if item.source_id not in states:
                states[item.source_id] = session.get(NotificationSyncStateRecord, item.source_id)
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
                    created_at=database_datetime(item.created_at),
                )
                session.add(record)
            update_hour_by_hour_record(record, item)

        items_by_source: dict[str, list[HourByHourItem]] = {}
        for item in items:
            items_by_source.setdefault(item.source_id, []).append(item)

        for source_id, state in states.items():
            current_hash = content_hash(items_by_source[source_id])
            if state is None:
                session.add(
                    NotificationSyncStateRecord(
                        source_id=source_id,
                        initialized_at=now,
                        last_synced_at=now,
                        last_content_hash=current_hash,
                    )
                )
                baseline_created = True
            else:
                state.last_synced_at = now
                state.last_content_hash = current_hash

        baseline_sources = {source_id for source_id, state in states.items() if state is None}
        for item in items:
            existing = session.scalar(
                select(NotificationOutboxRecord.id).where(
                    NotificationOutboxRecord.event_type == "hour_by_hour",
                    NotificationOutboxRecord.source_id == item.source_id,
                    NotificationOutboxRecord.external_id == item.external_id,
                )
            )
            if existing is not None:
                continue
            outbox = NotificationOutboxRecord(
                id=str(uuid4()),
                event_type="hour_by_hour",
                source_id=item.source_id,
                external_id=item.external_id,
                title=item.display_title or item.title,
                body=item.summary or item.title,
                url=item.action_url or item.article_url,
                collapse_id=collapse_id(item.external_id),
                created_at=now,
            )
            session.add(outbox)
            if item.source_id in baseline_sources:
                continue
            notifications_created += 1
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
