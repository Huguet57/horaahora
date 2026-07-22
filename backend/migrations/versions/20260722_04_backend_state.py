"""Centralize notification and rate-limit state in PostgreSQL."""

from alembic import op
import sqlalchemy as sa


revision = "20260722_04"
down_revision = "20260721_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_index("ix_push_subscriptions_installation_id", "push_subscriptions", ["installation_id"])
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
        sa.UniqueConstraint(
            "outbox_id", "subscription_id", name="uq_notification_delivery_target"
        ),
    )
    op.create_index("ix_notification_deliveries_outbox_id", "notification_deliveries", ["outbox_id"])
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
    op.create_index("ix_notification_deliveries_created_at", "notification_deliveries", ["created_at"])
    op.create_index("ix_notification_deliveries_updated_at", "notification_deliveries", ["updated_at"])

    op.create_table(
        "rate_limit_buckets",
        sa.Column("identifier_hash", sa.String(length=64), primary_key=True),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rate_limit_buckets_expires_at", "rate_limit_buckets", ["expires_at"])


def downgrade() -> None:
    op.drop_table("rate_limit_buckets")
    op.drop_table("notification_deliveries")
    op.drop_table("notification_outbox")
    op.drop_table("notification_sync_state")
    op.drop_table("push_subscriptions")
