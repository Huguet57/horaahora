from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

MOVED_TABLES = {
    "hour_by_hour_items",
    "agenda_events",
    "agenda_syncs",
    "push_subscriptions",
    "notification_sync_state",
    "notification_outbox",
    "notification_deliveries",
}


def _config(tmp_path, monkeypatch, name: str) -> tuple[Config, str]:
    database_url = f"sqlite+pysqlite:///{tmp_path / name}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    return Config(str(Path(__file__).parents[2] / "alembic.ini")), database_url


def test_migrations_create_only_the_calculator_tables(tmp_path, monkeypatch) -> None:
    config, database_url = _config(tmp_path, monkeypatch, "migration.db")

    command.upgrade(config, "head")

    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert tables == {"alembic_version", "rate_limit_buckets", "shared_conversations"}
    command.check(config)


def test_dropping_the_moved_tables_keeps_the_calculator_rows(tmp_path, monkeypatch) -> None:
    config, database_url = _config(tmp_path, monkeypatch, "upgrade.db")
    command.upgrade(config, "20260927_09")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("""INSERT INTO shared_conversations (id, conversation_id, messages, created_at)
            VALUES ('shared', 'conversation', '[]', CURRENT_TIMESTAMP)""")
        )
        connection.execute(
            text("""INSERT INTO rate_limit_buckets
            (identifier_hash, window_started_at, request_count, expires_at)
            VALUES ('hash', CURRENT_TIMESTAMP, 1, CURRENT_TIMESTAMP)""")
        )

    command.upgrade(config, "head")

    assert not MOVED_TABLES & set(inspect(engine).get_table_names())
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT id FROM shared_conversations")) == "shared"
        assert connection.scalar(text("SELECT identifier_hash FROM rate_limit_buckets")) == "hash"


def test_downgrade_recreates_the_moved_tables_as_they_were(tmp_path, monkeypatch) -> None:
    config, database_url = _config(tmp_path, monkeypatch, "downgrade.db")
    command.upgrade(config, "20260927_09")
    engine = create_engine(database_url)
    before = _schema(engine)

    command.upgrade(config, "head")
    command.downgrade(config, "20260927_09")

    assert _schema(engine) == before
    command.downgrade(config, "base")


def _schema(engine) -> dict[str, tuple]:
    inspector = inspect(engine)
    return {
        table: (
            sorted(
                (column["name"], str(column["type"]), column["nullable"], column["default"])
                for column in inspector.get_columns(table)
            ),
            sorted(index["name"] for index in inspector.get_indexes(table)),
            sorted(
                str(constraint["name"]) for constraint in inspector.get_unique_constraints(table)
            ),
            sorted(
                (key["referred_table"], tuple(key["constrained_columns"]))
                for key in inspector.get_foreign_keys(table)
            ),
        )
        for table in MOVED_TABLES
    }
