from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import RateLimitBucketRecord
from backend.adapters.rate_limit.postgres import PostgresRateLimiter

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
PUBLIC_TABLES = {"alembic_version", "rate_limit_buckets", "shared_conversations"}
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
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))

    # Exercise both supported deployment paths: upgrading the previous revision
    # and applying the complete migration chain to an empty database. The round trip
    # through the previous revision also recreates the tables Hora a Hora took with it.
    command.downgrade(config, "base")
    command.upgrade(config, "20260927_09")
    command.upgrade(config, "head")
    command.downgrade(config, "20260927_09")
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
    assert set(inspect(postgres_database.engine).get_table_names()) == PUBLIC_TABLES


def test_postgres_migrations_enable_rls_on_every_public_table(
    postgres_database: Database,
) -> None:
    with postgres_database.engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT cls.relname, cls.relrowsecurity
                FROM pg_class AS cls
                JOIN pg_namespace AS namespace ON namespace.oid = cls.relnamespace
                WHERE namespace.nspname = 'public'
                  AND cls.relkind IN ('r', 'p')
                """
            )
        )

        rls_by_table = {row.relname: row.relrowsecurity for row in rows}

    assert PUBLIC_TABLES <= rls_by_table.keys()
    assert {table for table, enabled in rls_by_table.items() if not enabled} == set()


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
