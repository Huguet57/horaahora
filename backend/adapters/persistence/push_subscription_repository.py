from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import PushSubscriptionRecord
from backend.adapters.persistence.notification_support import revoked_token
from backend.adapters.persistence.repository_support import resolve_engine
from backend.domain.notifications.models import (
    ActivePushSubscription,
    PushSubscriptionRegistration,
)


class SQLAlchemyPushSubscriptionRepository:
    def __init__(self, database: Database) -> None:
        self.database, self.engine = resolve_engine(database)

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
                _invalidate(collision, now)

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
                _invalidate(record, now)

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


def _invalidate(record: PushSubscriptionRecord, now: datetime) -> None:
    record.hour_by_hour_enabled = False
    record.invalidated_at = now
    record.updated_at = now
    record.device_token = revoked_token(record.id)
