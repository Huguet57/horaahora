from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.adapters.persistence.models import (
    AgendaEventRecord,
    NotificationDeliveryRecord,
    NotificationOutboxRecord,
    PushSubscriptionRecord,
)
from backend.domain.notifications.interest import (
    ClassificationCandidate,
    GroupSelection,
    InterestClassification,
    InterestLevel,
    qualifies,
)


class NewsClassificationPersistence:
    def __init__(self, engine):
        self.engine = engine

    def recover_interrupted(self) -> int:
        # Both ingestion entrypoints hold the same advisory lock. A processing row
        # therefore belongs to an interrupted previous run, never a concurrent request.
        with Session(self.engine) as session, session.begin():
            result = session.execute(
                update(NotificationOutboxRecord)
                .where(NotificationOutboxRecord.classification_status == "processing")
                .values(
                    classification_status="skipped", classification_error="Interrupted", audience=[]
                )
            )
            return result.rowcount or 0

    def pending(self) -> list[ClassificationCandidate]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(NotificationOutboxRecord)
                .where(NotificationOutboxRecord.classification_status == "pending")
                .order_by(NotificationOutboxRecord.created_at, NotificationOutboxRecord.id)
            ).all()
            return [ClassificationCandidate(row.id, row.title, row.body) for row in rows]

    def begin(self, outbox_id: str) -> bool:
        with Session(self.engine) as session, session.begin():
            result = session.execute(
                update(NotificationOutboxRecord)
                .where(
                    NotificationOutboxRecord.id == outbox_id,
                    NotificationOutboxRecord.classification_status == "pending",
                )
                .values(classification_status="processing")
            )
            return result.rowcount == 1

    def skip(self, outbox_id: str, reason: str) -> None:
        with Session(self.engine) as session, session.begin():
            session.execute(
                update(NotificationOutboxRecord)
                .where(
                    NotificationOutboxRecord.id == outbox_id,
                    NotificationOutboxRecord.classification_status == "processing",
                )
                .values(
                    classification_status="skipped", classification_error=reason[:100], audience=[]
                )
            )

    def complete(self, outbox_id: str, result: InterestClassification) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as session, session.begin():
            outbox = session.get(NotificationOutboxRecord, outbox_id)
            if outbox is None or outbox.classification_status != "processing":
                return
            outbox.classification = {
                "level": result.level.value,
                "group_keys": sorted(result.group_keys),
                "model": result.model,
                "criteria_version": result.criteria_version,
                "probabilities": result.probabilities,
                "confidence": result.confidence,
                "usage": result.usage,
            }
            outbox.classification_status = "classified"
            for recipient in outbox.audience:
                subscription = session.get(PushSubscriptionRecord, recipient["id"])
                if (
                    subscription is None
                    or not subscription.hour_by_hour_enabled
                    or subscription.invalidated_at is not None
                ):
                    continue
                # Freeze the audience and preferences at discovery. Later selections
                # may suppress a pending delivery, but cannot create retrospective ones.
                if not qualifies(
                    result.level,
                    result.group_keys,
                    InterestLevel(recipient["minimum_interest"]),
                    GroupSelection.from_json(recipient["group_selection"]),
                ):
                    continue
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
            outbox.audience = []

    def observed_groups(self) -> list[str]:
        with Session(self.engine) as session:
            groups = session.scalars(select(AgendaEventRecord.participating_groups)).all()
            return sorted({name for names in groups for name in names})


def subscription_qualifies(outbox: NotificationOutboxRecord, subscription: PushSubscriptionRecord):
    if outbox.classification_status == "legacy":
        # Already queued before the migration: preserve old low subscriptions only.
        return subscription.minimum_interest == "low"
    if outbox.classification_status != "classified" or outbox.classification is None:
        return False
    return qualifies(
        InterestLevel(outbox.classification["level"]),
        frozenset(outbox.classification["group_keys"]),
        InterestLevel(subscription.minimum_interest),
        GroupSelection.from_json(subscription.group_selection),
    )
