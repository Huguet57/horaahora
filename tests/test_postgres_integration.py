from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.notifications import SQLAlchemyNotificationRepository
from backend.adapters.persistence.sqlalchemy import RateLimitBucketRecord
from backend.adapters.rate_limit.postgres import PostgresRateLimiter
from backend.domain.models import HourByHourItem, PushSubscriptionRegistration


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL no està configurada per a la integració PostgreSQL",
)


@pytest.fixture(scope="module")
def postgres_database(monkeypatch_module: pytest.MonkeyPatch) -> Database:
    database_name = make_url(TEST_DATABASE_URL).database or ""
    if not database_name.endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL ha d'apuntar a una base acabada en _test")

    monkeypatch_module.setenv("DATABASE_URL", TEST_DATABASE_URL)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))

    # Exercise both supported deployment paths: upgrading the previous revision
    # and applying the complete migration chain to an empty database.
    command.downgrade(config, "base")
    command.upgrade(config, "20260721_03")
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return Database(TEST_DATABASE_URL)


@pytest.fixture(scope="module")
def monkeypatch_module() -> pytest.MonkeyPatch:
    patch = pytest.MonkeyPatch()
    yield patch
    patch.undo()


def test_postgres_migrations_create_the_complete_backend_schema(
    postgres_database: Database,
) -> None:
    assert {
        "hour_by_hour_items",
        "agenda_events",
        "agenda_syncs",
        "push_subscriptions",
        "notification_sync_state",
        "notification_outbox",
        "notification_deliveries",
        "rate_limit_buckets",
    } <= set(inspect(postgres_database.engine).get_table_names())


def test_postgres_rate_limiter_is_atomic_under_concurrency(
    postgres_database: Database,
) -> None:
    limiter = PostgresRateLimiter(
        postgres_database,
        hash_secret="integration-secret",
        max_requests=5,
        window_seconds=60,
    )

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda _: limiter.allow("same-installation"), range(20)))

    assert sum(1 for allowed, _ in results if allowed) == 5
    with Session(postgres_database.engine) as session:
        bucket = session.scalar(select(RateLimitBucketRecord))
    assert bucket is not None
    assert bucket.request_count == 20
    assert "same-installation" not in bucket.identifier_hash


def test_postgres_advisory_lock_rejects_a_duplicate_cron(
    postgres_database: Database,
) -> None:
    second_database = Database(TEST_DATABASE_URL)

    with postgres_database.advisory_lock(849_301) as first_acquired:
        with second_database.advisory_lock(849_301) as second_acquired:
            assert first_acquired is True
            assert second_acquired is False

    with second_database.advisory_lock(849_301) as acquired_after_release:
        assert acquired_after_release is True


def test_postgres_skip_locked_claims_each_delivery_once(
    postgres_database: Database,
) -> None:
    repository = SQLAlchemyNotificationRepository(postgres_database)
    repository.register(
        PushSubscriptionRegistration(
            installation_id="postgres-integration-installation",
            device_token="ef" * 32,
            app_version="1.0 (1)",
            locale="ca-ES",
        ),
        environment="production",
        topic="com.example.integration",
    )
    repository.ingest_hour_by_hour([_item("postgres-baseline")])
    repository.ingest_hour_by_hour(
        [_item("postgres-new-item"), _item("postgres-baseline")]
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        claims = list(executor.map(lambda _: repository.claim_deliveries(limit=1), range(2)))

    assert sum(len(claim) for claim in claims) == 1


def _item(external_id: str) -> HourByHourItem:
    now = datetime.now(UTC)
    return HourByHourItem(
        id=external_id,
        source_id="postgres-integration-source",
        external_id=external_id,
        title=f"Notícia {external_id}",
        display_title=f"Notícia {external_id}",
        summary="Resum",
        published_at=now,
        source_order=0,
        article_url=f"https://example.com/{external_id}",
        action_url=f"https://example.com/{external_id}/directe",
        attribution="Test",
        created_at=now,
        updated_at=now,
    )
