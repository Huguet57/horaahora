from __future__ import annotations

import pytest
from sqlalchemy.pool import NullPool

from backend.adapters.persistence.database import Database, normalize_database_url
from backend.config import Settings


def test_neon_url_uses_the_installed_psycopg3_driver() -> None:
    assert normalize_database_url(
        "postgresql://user:secret@ep-example.eu-central-1.aws.neon.tech/app?sslmode=require"
    ) == (
        "postgresql+psycopg://user:secret@"
        "ep-example.eu-central-1.aws.neon.tech/app?sslmode=require"
    )
    assert normalize_database_url("postgres://user:secret@host/app") == (
        "postgresql+psycopg://user:secret@host/app"
    )


def test_neon_proxy_owns_pooling() -> None:
    database = Database("postgresql://user:secret@localhost/horaahora_test")

    assert isinstance(database.engine.pool, NullPool)


def test_runtime_settings_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        Settings.from_env()


def test_runtime_settings_reject_sqlite_even_outside_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("RATE_LIMIT_HASH_SECRET", "test-secret")

    with pytest.raises(RuntimeError, match="PostgreSQL"):
        Settings.from_env()


def test_preview_can_never_deliver_real_pushes() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:secret@host/app",
        vercel_env="preview",
        push_delivery_enabled=True,
    )

    assert settings.can_deliver_push is False
    assert settings.apns_environment == "development"


def test_database_readiness_executes_a_real_query() -> None:
    database = Database("sqlite+pysqlite:///:memory:")

    assert database.is_ready() is True
