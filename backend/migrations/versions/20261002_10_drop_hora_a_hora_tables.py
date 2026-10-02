"""Drop the Hora a Hora, Agenda and push notification tables: they moved to Hora a Hora.

The news feed, the Agenda and the news notifications now live in the Hora a Hora repository,
with their own backend and database. This backend keeps only the calculator state
(rate_limit_buckets and shared_conversations).

Only run this in production after the data of these tables has been copied to the new
Hora a Hora database: the upgrade deletes it for good. The downgrade recreates the tables
exactly as revision 20260927_09 left them, but empty; restoring their rows means copying
them back from the Hora a Hora database.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261002_10"
down_revision = "20260927_09"
branch_labels = None
depends_on = None

# Children before parents: notification_deliveries references the outbox and the subscriptions.
MOVED_TABLES = (
    "notification_deliveries",
    "notification_outbox",
    "notification_sync_state",
    "push_subscriptions",
    "agenda_syncs",
    "agenda_events",
    "hour_by_hour_items",
)
SUPABASE_API_ROLES = ("anon", "authenticated")


def upgrade() -> None:
    for table in MOVED_TABLES:
        op.drop_table(table)


def downgrade() -> None:
    _create_hour_by_hour_items()
    _create_agenda_tables()
    _create_notification_tables()
    _protect_from_supabase_api(reversed(MOVED_TABLES))


def _create_hour_by_hour_items() -> None:
    op.create_table(
        "hour_by_hour_items",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_order", sa.Integer(), nullable=False),
        sa.Column("article_url", sa.Text(), nullable=False),
        sa.Column("action_url", sa.Text(), nullable=False),
        sa.Column("attribution", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("display_title", sa.Text(), nullable=False),
        sa.UniqueConstraint("source_id", "external_id", name="uq_hour_by_hour_source_external"),
    )
    op.create_index("ix_hour_by_hour_items_source_id", "hour_by_hour_items", ["source_id"])
    op.create_index("ix_hour_by_hour_items_published_at", "hour_by_hour_items", ["published_at"])
    op.create_index("ix_hour_by_hour_items_updated_at", "hour_by_hour_items", ["updated_at"])


def _create_agenda_tables() -> None:
    op.create_table(
        "agenda_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_label", sa.String(length=50), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("venue", sa.Text(), nullable=False),
        sa.Column("municipality", sa.String(length=200), nullable=False),
        sa.Column("participating_groups", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_order", sa.Integer(), nullable=False),
        sa.Column("attribution", sa.String(length=250), nullable=False),
        sa.Column("revision", sa.String(length=128), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_id", "external_id", name="uq_agenda_source_external"),
    )
    op.create_index("ix_agenda_events_source_id", "agenda_events", ["source_id"])
    op.create_index("ix_agenda_events_local_date", "agenda_events", ["local_date"])
    op.create_index("ix_agenda_events_municipality", "agenda_events", ["municipality"])
    op.create_index("ix_agenda_events_updated_at", "agenda_events", ["updated_at"])

    op.create_table(
        "agenda_syncs",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agenda_syncs_source_id", "agenda_syncs", ["source_id"])
    op.create_index("ix_agenda_syncs_synced_at", "agenda_syncs", ["synced_at"])


def _create_notification_tables() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("installation_id", sa.String(length=128), nullable=False),
        sa.Column("device_token", sa.Text(), nullable=False),
        sa.Column("environment", sa.String(length=20), nullable=False),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("hour_by_hour_enabled", sa.Boolean(), nullable=False),
        sa.Column("app_version", sa.String(length=64), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("minimum_interest", sa.String(10), nullable=False, server_default="low"),
        sa.Column(
            "group_selection", sa.JSON(), nullable=False, server_default='{"mode":"all","keys":[]}'
        ),
        sa.Column("platform", sa.String(length=20), nullable=False, server_default="ios"),
        sa.UniqueConstraint(
            "installation_id",
            "environment",
            "topic",
            name="uq_push_installation_environment_topic",
        ),
        sa.UniqueConstraint(
            "device_token", "environment", "topic", name="uq_push_token_environment_topic"
        ),
    )
    op.create_index(
        "ix_push_subscriptions_installation_id", "push_subscriptions", ["installation_id"]
    )
    op.create_index("ix_push_subscriptions_environment", "push_subscriptions", ["environment"])
    op.create_index("ix_push_subscriptions_updated_at", "push_subscriptions", ["updated_at"])
    op.create_index("ix_push_subscriptions_last_seen_at", "push_subscriptions", ["last_seen_at"])

    op.create_table(
        "notification_sync_state",
        sa.Column("source_id", sa.String(length=100), primary_key=True),
        sa.Column("initialized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_content_hash", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_notification_sync_state_last_synced_at",
        "notification_sync_state",
        ["last_synced_at"],
    )

    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("collapse_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("classification_status", sa.String(20), nullable=False, server_default="legacy"),
        sa.Column("classification", sa.JSON(), nullable=True),
        sa.Column("classification_error", sa.String(100), nullable=False, server_default=""),
        sa.Column("audience", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("article_url", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint(
            "event_type", "source_id", "external_id", name="uq_notification_outbox_event"
        ),
    )
    op.create_index("ix_notification_outbox_event_type", "notification_outbox", ["event_type"])
    op.create_index("ix_notification_outbox_source_id", "notification_outbox", ["source_id"])
    op.create_index("ix_notification_outbox_created_at", "notification_outbox", ["created_at"])

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "outbox_id",
            sa.String(length=36),
            sa.ForeignKey("notification_outbox.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.String(length=36),
            sa.ForeignKey("push_subscriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("outbox_id", "subscription_id", name="uq_notification_delivery_target"),
    )
    op.create_index(
        "ix_notification_deliveries_outbox_id", "notification_deliveries", ["outbox_id"]
    )
    op.create_index(
        "ix_notification_deliveries_subscription_id",
        "notification_deliveries",
        ["subscription_id"],
    )
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"])
    op.create_index(
        "ix_notification_deliveries_next_attempt_at",
        "notification_deliveries",
        ["next_attempt_at"],
    )
    op.create_index(
        "ix_notification_deliveries_created_at", "notification_deliveries", ["created_at"]
    )
    op.create_index(
        "ix_notification_deliveries_updated_at", "notification_deliveries", ["updated_at"]
    )


def _protect_from_supabase_api(tables) -> None:
    # Same protection as 20260903_05: row level security on, no access for the Data API roles.
    connection = op.get_bind()
    if connection.dialect.name != "postgresql":
        return
    existing_api_roles = set(
        connection.scalars(
            sa.text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
        )
    )
    for table in tables:
        op.execute(sa.text(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY'))
        for role in SUPABASE_API_ROLES:
            if role in existing_api_roles:
                op.execute(
                    sa.text(f'REVOKE ALL PRIVILEGES ON TABLE public."{table}" FROM "{role}"')
                )
