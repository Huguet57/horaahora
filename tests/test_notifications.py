from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.sqlalchemy import (
    Base,
    NotificationDeliveryRecord,
    NotificationOutboxRecord,
    NotificationSyncStateRecord,
    PushSubscriptionRecord,
    SQLAlchemyContentRepository,
)
from backend.adapters.persistence.notifications import SQLAlchemyNotificationRepository
from backend.application.notifications import HourByHourNotificationCoordinator
from backend.domain.models import HourByHourItem, PushSubscriptionRegistration


def hour_item(external_id: str, title: str | None = None) -> HourByHourItem:
    now = datetime.now(UTC)
    return HourByHourItem(
        id=external_id,
        source_id="revista-castells",
        external_id=external_id,
        title=title or f"Dimecres 22, 10h. Notícia {external_id}",
        display_title=f"Notícia {external_id}",
        summary=f"Resum {external_id}",
        published_at=now,
        source_order=0,
        article_url=f"https://example.com/{external_id}",
        action_url=f"https://example.com/{external_id}/directe",
        attribution="Revista Castells",
        created_at=now,
        updated_at=now,
    )


def repository() -> SQLAlchemyNotificationRepository:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return SQLAlchemyNotificationRepository(database)


def registration(token: str = "ab" * 32) -> PushSubscriptionRegistration:
    return PushSubscriptionRegistration(
        installation_id="installation-1",
        device_token=token,
        app_version="1.0 (3)",
        locale="ca-ES",
    )


def test_subscription_registration_is_idempotent_and_rotates_the_token() -> None:
    repo = repository()

    repo.register(registration(), environment="production", topic="com.example.app")
    repo.register(registration("cd" * 32), environment="production", topic="com.example.app")

    subscriptions = repo.list_active_subscriptions()
    assert len(subscriptions) == 1
    assert subscriptions[0].device_token == "cd" * 32

    repo.unregister("installation-1", environment="production", topic="com.example.app")
    assert repo.list_active_subscriptions() == []
    with Session(repo.engine) as session:
        stored_token = session.scalar(select(PushSubscriptionRecord.device_token))
    assert stored_token != "cd" * 32


def test_first_ingestion_is_a_baseline_and_next_item_creates_one_delivery() -> None:
    repo = repository()
    repo.register(registration(), environment="production", topic="com.example.app")

    baseline = repo.ingest_hour_by_hour([hour_item("one")])
    update = repo.ingest_hour_by_hour([hour_item("two"), hour_item("one")])
    repeated = repo.ingest_hour_by_hour([hour_item("two"), hour_item("one")])

    assert baseline.baseline_created is True
    assert baseline.notifications_created == 0
    assert update.notifications_created == 1
    assert repeated.notifications_created == 0

    deliveries = repo.claim_deliveries(limit=10, lock_seconds=60)
    assert len(deliveries) == 1
    assert deliveries[0].title == "Notícia two"
    assert deliveries[0].url == "https://example.com/two/directe"
    with Session(repo.engine) as session:
        state = session.get(NotificationSyncStateRecord, "revista-castells")
    assert state is not None
    assert len(state.last_content_hash) == 64


def test_content_refresh_before_cron_does_not_consume_the_notification() -> None:
    repo = repository()
    repo.register(registration(), environment="production", topic="com.example.app")
    repo.ingest_hour_by_hour([hour_item("one")])

    content_repository = SQLAlchemyContentRepository(repo.database)
    content_repository.upsert_hour_by_hour([hour_item("two"), hour_item("one")])

    update = repo.ingest_hour_by_hour([hour_item("two"), hour_item("one")])
    repeated = repo.ingest_hour_by_hour([hour_item("two"), hour_item("one")])

    assert update.notifications_created == 1
    assert repeated.notifications_created == 0
    assert len(repo.claim_deliveries(limit=10)) == 1


def test_transient_delivery_is_retried_and_invalid_token_disables_subscription() -> None:
    repo = repository()
    repo.register(registration(), environment="production", topic="com.example.app")
    repo.ingest_hour_by_hour([hour_item("one")])
    repo.ingest_hour_by_hour([hour_item("two"), hour_item("one")])
    delivery = repo.claim_deliveries(limit=1, lock_seconds=60)[0]

    retry_at = datetime.now(UTC) + timedelta(minutes=1)
    repo.mark_retry(delivery.id, reason="TooManyRequests", retry_at=retry_at)
    assert repo.claim_deliveries(limit=1, now=retry_at - timedelta(seconds=1)) == []

    retried = repo.claim_deliveries(limit=1, now=retry_at + timedelta(seconds=1))[0]
    repo.mark_invalid_token(retried, reason="Unregistered")

    assert repo.list_active_subscriptions() == []
    assert repo.claim_deliveries(limit=10, now=retry_at + timedelta(minutes=2)) == []


def test_interrupted_claim_becomes_available_after_its_lock_expires() -> None:
    repo = repository()
    repo.register(registration(), environment="production", topic="com.example.app")
    repo.ingest_hour_by_hour([hour_item("one")])
    repo.ingest_hour_by_hour([hour_item("two"), hour_item("one")])
    claimed_at = datetime.now(UTC)

    first = repo.claim_deliveries(limit=1, now=claimed_at, lock_seconds=60)
    while_locked = repo.claim_deliveries(
        limit=1, now=claimed_at + timedelta(seconds=59)
    )
    recovered = repo.claim_deliveries(
        limit=1, now=claimed_at + timedelta(seconds=61)
    )

    assert len(first) == 1
    assert while_locked == []
    assert len(recovered) == 1
    assert recovered[0].id == first[0].id
    assert recovered[0].attempt_count == 2


def test_maintenance_expires_personal_state_but_keeps_outbox_deduplication() -> None:
    repo = repository()
    repo.register(registration(), environment="production", topic="com.example.app")
    repo.ingest_hour_by_hour([hour_item("one")])
    repo.ingest_hour_by_hour([hour_item("two"), hour_item("one")])
    delivery = repo.claim_deliveries(limit=1)[0]
    repo.mark_delivered(delivery.id)

    now = datetime.now(UTC)
    with Session(repo.engine) as session, session.begin():
        subscription = session.scalar(select(PushSubscriptionRecord))
        stored_delivery = session.get(NotificationDeliveryRecord, delivery.id)
        assert subscription is not None and stored_delivery is not None
        subscription.last_seen_at = (now - timedelta(days=181)).replace(tzinfo=None)
        stored_delivery.created_at = (now - timedelta(days=31)).replace(tzinfo=None)

    counts = repo.cleanup(now=now)

    assert counts == {
        "subscriptions_invalidated": 1,
        "deliveries_deleted": 1,
        "outboxes_deleted": 0,
    }
    with Session(repo.engine) as session:
        outbox_count = session.scalar(
            select(func.count()).select_from(NotificationOutboxRecord)
        )
    assert outbox_count == 2
    assert repo.list_active_subscriptions() == []


class MutableSource:
    def __init__(self, items: list[HourByHourItem]) -> None:
        self.items = items
        self.fetch_count = 0

    def fetch(self) -> list[HourByHourItem]:
        self.fetch_count += 1
        return self.items


class AcceptingGateway:
    def __init__(self) -> None:
        self.deliveries = []

    def send(self, delivery):
        from backend.domain.models import NotificationDisposition, NotificationSendResult

        self.deliveries.append(delivery)
        return NotificationSendResult(NotificationDisposition.DELIVERED)


def test_coordinator_is_idempotent_and_does_nothing_while_disabled() -> None:
    repo = repository()
    repo.register(registration(), environment="production", topic="com.example.app")
    source = MutableSource([hour_item("one")])
    gateway = AcceptingGateway()
    coordinator = HourByHourNotificationCoordinator(repo, source, gateway, enabled=False)

    disabled = coordinator.run()
    assert disabled.status == "disabled"
    assert source.fetch_count == 0

    coordinator.enabled = True
    coordinator.run()
    source.items = [hour_item("two"), hour_item("one")]
    sent = coordinator.run()
    repeated = coordinator.run()

    assert sent.delivered == 1
    assert repeated.delivered == 0
    assert len(gateway.deliveries) == 1
