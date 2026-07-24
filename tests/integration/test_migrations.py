from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_migrations_create_all_neon_backend_state_tables(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+pysqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))

    command.upgrade(config, "head")

    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert {
        "hour_by_hour_items",
        "agenda_events",
        "agenda_syncs",
        "push_subscriptions",
        "notification_sync_state",
        "notification_outbox",
        "notification_deliveries",
        "rate_limit_buckets",
    } <= tables
