from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.sqlalchemy import Base, RateLimitBucketRecord
from backend.adapters.rate_limit.postgres import PostgresRateLimiter


def test_sql_rate_limiter_hashes_identifiers_and_resets_after_the_window() -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    now = datetime(2026, 7, 22, 10, 0, tzinfo=UTC)
    limiter = PostgresRateLimiter(
        database,
        hash_secret="test-secret",
        max_requests=2,
        window_seconds=60,
        clock=lambda: now,
    )

    assert limiter.allow("192.0.2.1:installation") == (True, 60)
    assert limiter.allow("192.0.2.1:installation") == (True, 60)
    allowed, retry_after = limiter.allow("192.0.2.1:installation")
    assert allowed is False
    assert retry_after == 60

    with Session(database.engine) as session:
        record = session.scalar(select(RateLimitBucketRecord))
        assert record is not None
        assert record.identifier_hash != "192.0.2.1:installation"
        assert len(record.identifier_hash) == 64

    now += timedelta(seconds=61)
    assert limiter.allow("192.0.2.1:installation") == (True, 60)


def test_cleanup_removes_expired_rate_limit_buckets() -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    now = datetime(2026, 7, 22, 10, 0, tzinfo=UTC)
    limiter = PostgresRateLimiter(
        database,
        hash_secret="test-secret",
        max_requests=2,
        window_seconds=60,
        clock=lambda: now,
    )
    limiter.allow("identifier")

    assert limiter.cleanup_expired(now=now + timedelta(minutes=2)) == 1
