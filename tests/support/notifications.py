from dataclasses import replace
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.persistence.models import NotificationDeliveryRecord, PushSubscriptionRecord
from backend.application.notification_ingestion import NotificationIngestionService
from backend.domain.notifications.interest import InterestClassification, InterestLevel
from backend.domain.notifications.models import PushSubscriptionRegistration
from tests.support.hour_by_hour import hour_item


class RoutineNewsClassifier:
    def classify(self, title, summary, groups, *, timeout, content=None):
        return InterestClassification(InterestLevel.LOW, frozenset(), "fake", "test", {}, 1.0)


def ingestion_service(repository):
    return NotificationIngestionService(repository, RoutineNewsClassifier(), [])


def ingest(repository, items):
    return ingestion_service(repository).ingest(items)


def queue_recipients_before_threshold_changes(subscriptions, repo, eligibility):
    registrations = [
        PushSubscriptionRegistration(
            device_token=f"{index + 1:064x}",
            app_version="1.0 (1)",
            locale="ca-ES",
            installation_id=f"refill-{index}",
            minimum_interest=InterestLevel.LOW,
        )
        for index in range(len(eligibility))
    ]
    for recipient in registrations:
        subscriptions.register(recipient, environment="production", topic="app")
    service = ingestion_service(repo)
    service.ingest([hour_item("baseline")])
    service.ingest([hour_item("new")])
    for recipient, eligible in zip(registrations, eligibility, strict=True):
        subscriptions.register(
            replace(
                recipient, minimum_interest=InterestLevel.LOW if eligible else InterestLevel.HIGH
            ),
            environment="production",
            topic="app",
        )
    with Session(repo.engine) as session, session.begin():
        for delivery, subscription in session.execute(
            select(NotificationDeliveryRecord, PushSubscriptionRecord)
            .where(
                PushSubscriptionRecord.installation_id.in_(
                    [recipient.installation_id for recipient in registrations]
                )
            )
            .join(
                PushSubscriptionRecord,
                PushSubscriptionRecord.id == NotificationDeliveryRecord.subscription_id,
            )
        ).all():
            # Equal timestamps exercise the ID tie-breaker across multiple pages.
            delivery.id = subscription.installation_id.replace("refill-", "queued-")
            delivery.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    return service
