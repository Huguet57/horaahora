from __future__ import annotations

import hashlib
import hmac
import math
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import RateLimitBucketRecord


class PostgresRateLimiter:
    def __init__(
        self,
        database: Database,
        *,
        hash_secret: str,
        max_requests: int = 30,
        window_seconds: int = 600,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not hash_secret:
            raise RuntimeError("RATE_LIMIT_HASH_SECRET és obligatori")
        self.database = database
        self.hash_secret = hash_secret.encode("utf-8")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock or (lambda: datetime.now(UTC))

    def allow(self, identifier: str) -> tuple[bool, int]:
        now = _utc(self.clock())
        expires_at = now + timedelta(seconds=self.window_seconds)
        identifier_hash = hmac.new(
            self.hash_secret, identifier.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if self.database.engine.dialect.name == "postgresql":
            count, stored_expiry = self._allow_postgres(
                identifier_hash, now, expires_at
            )
        else:
            count, stored_expiry = self._allow_sqlite_for_tests(
                identifier_hash, now, expires_at
            )
        retry_after = max(1, math.ceil((_utc(stored_expiry) - now).total_seconds()))
        return count <= self.max_requests, retry_after

    def cleanup_expired(self, *, now: datetime | None = None) -> int:
        cutoff = _database_datetime(now or self.clock())
        with Session(self.database.engine) as session, session.begin():
            result = session.execute(
                delete(RateLimitBucketRecord).where(
                    RateLimitBucketRecord.expires_at <= cutoff
                )
            )
            return result.rowcount or 0

    def _allow_postgres(
        self, identifier_hash: str, now: datetime, expires_at: datetime
    ) -> tuple[int, datetime]:
        statement = text(
            """
            INSERT INTO rate_limit_buckets
                (identifier_hash, window_started_at, request_count, expires_at)
            VALUES (:identifier_hash, :now, 1, :expires_at)
            ON CONFLICT (identifier_hash) DO UPDATE SET
                window_started_at = CASE
                    WHEN rate_limit_buckets.expires_at <= EXCLUDED.window_started_at
                    THEN EXCLUDED.window_started_at
                    ELSE rate_limit_buckets.window_started_at
                END,
                request_count = CASE
                    WHEN rate_limit_buckets.expires_at <= EXCLUDED.window_started_at
                    THEN 1
                    ELSE rate_limit_buckets.request_count + 1
                END,
                expires_at = CASE
                    WHEN rate_limit_buckets.expires_at <= EXCLUDED.window_started_at
                    THEN EXCLUDED.expires_at
                    ELSE rate_limit_buckets.expires_at
                END
            RETURNING request_count, expires_at
            """
        )
        with self.database.engine.begin() as connection:
            row = connection.execute(
                statement,
                {
                    "identifier_hash": identifier_hash,
                    "now": now,
                    "expires_at": expires_at,
                },
            ).one()
            return int(row.request_count), row.expires_at

    def _allow_sqlite_for_tests(
        self, identifier_hash: str, now: datetime, expires_at: datetime
    ) -> tuple[int, datetime]:
        database_now = _database_datetime(now)
        database_expiry = _database_datetime(expires_at)
        with Session(self.database.engine) as session, session.begin():
            record = session.scalar(
                select(RateLimitBucketRecord).where(
                    RateLimitBucketRecord.identifier_hash == identifier_hash
                )
            )
            if record is None:
                record = RateLimitBucketRecord(
                    identifier_hash=identifier_hash,
                    window_started_at=database_now,
                    request_count=1,
                    expires_at=database_expiry,
                )
                session.add(record)
            elif record.expires_at <= database_now:
                record.window_started_at = database_now
                record.request_count = 1
                record.expires_at = database_expiry
            else:
                record.request_count += 1
            session.flush()
            return record.request_count, record.expires_at


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _database_datetime(value: datetime) -> datetime:
    return _utc(value).replace(tzinfo=None)
