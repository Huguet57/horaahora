"""Stop the notification work of an Hora a Hora item that has been withdrawn."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.adapters.persistence.models import NotificationDeliveryRecord, NotificationOutboxRecord

_UNCLASSIFIED = ("pending", "processing")
_UNDELIVERED = ("pending", "retry", "processing")


def cancel_undelivered_notifications(
    session: Session, *, source_id: str, external_id: str, reason: str, now: datetime
) -> int:
    outbox_ids = session.scalars(
        select(NotificationOutboxRecord.id).where(
            NotificationOutboxRecord.event_type == "hour_by_hour",
            NotificationOutboxRecord.source_id == source_id,
            NotificationOutboxRecord.external_id == external_id,
        )
    ).all()
    if not outbox_ids:
        return 0
    # Without an audience, a classification that finishes later creates no deliveries.
    session.execute(
        update(NotificationOutboxRecord)
        .where(
            NotificationOutboxRecord.id.in_(outbox_ids),
            NotificationOutboxRecord.classification_status.in_(_UNCLASSIFIED),
        )
        .values(classification_status="skipped", classification_error=reason, audience=[])
    )
    return (
        session.execute(
            update(NotificationDeliveryRecord)
            .where(
                NotificationDeliveryRecord.outbox_id.in_(outbox_ids),
                NotificationDeliveryRecord.delivered_at.is_(None),
                NotificationDeliveryRecord.status.in_(_UNDELIVERED),
            )
            .values(status="skipped", last_error=reason, locked_until=None, updated_at=now)
        ).rowcount
        or 0
    )
