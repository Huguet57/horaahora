from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, StaticPool


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return database_url


class Database:
    _sqlite_advisory_lock = Lock()

    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise RuntimeError("DATABASE_URL és obligatòria")
        self.database_url = normalize_database_url(database_url)
        if self.database_url.startswith("sqlite"):
            engine_options: dict = {"connect_args": {"check_same_thread": False}}
            if ":memory:" in self.database_url:
                engine_options["poolclass"] = StaticPool
        else:
            engine_options = {"poolclass": NullPool, "pool_pre_ping": True}
        self.engine: Engine = create_engine(self.database_url, **engine_options)

    def is_ready(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @contextmanager
    def advisory_lock(self, key: int) -> Iterator[bool]:
        if self.engine.dialect.name != "postgresql":
            acquired = self._sqlite_advisory_lock.acquire(blocking=False)
            try:
                yield acquired
            finally:
                if acquired:
                    self._sqlite_advisory_lock.release()
            return

        with self.engine.connect() as connection:
            acquired = bool(
                connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": key})
            )
            try:
                yield acquired
            finally:
                if acquired:
                    connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
