from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_migrations_create_all_backend_state_tables(tmp_path, monkeypatch) -> None:
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


def test_interest_migration_preserves_existing_subscriptions(tmp_path, monkeypatch):
    url = f"sqlite+pysqlite:///{tmp_path / 'upgrade.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    command.upgrade(config, "20260903_05")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text("""INSERT INTO push_subscriptions
            (id, installation_id, device_token, environment, topic, hour_by_hour_enabled,
             app_version, locale, created_at, updated_at, last_seen_at)
            VALUES ('old', 'old', 'token', 'production', 'app', true, '1', 'ca',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""")
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT minimum_interest, group_selection FROM push_subscriptions")
        ).one()
        assert row.minimum_interest == "low"
        assert __import__("json").loads(row.group_selection) == {"mode": "all", "keys": []}
    command.check(config)
    command.downgrade(config, "20260903_05")
    assert "minimum_interest" not in {
        c["name"] for c in inspect(engine).get_columns("push_subscriptions")
    }
