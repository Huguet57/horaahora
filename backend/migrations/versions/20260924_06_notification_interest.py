"""Persist notification preferences and one classification per news item."""

import sqlalchemy as sa
from alembic import op

revision = "20260924_06"
down_revision = "20260903_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "push_subscriptions",
        sa.Column("minimum_interest", sa.String(10), nullable=False, server_default="low"),
    )
    op.add_column(
        "push_subscriptions",
        sa.Column(
            "group_selection", sa.JSON(), nullable=False, server_default='{"mode":"all","keys":[]}'
        ),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("classification_status", sa.String(20), nullable=False, server_default="legacy"),
    )
    op.add_column("notification_outbox", sa.Column("classification", sa.JSON(), nullable=True))
    op.add_column(
        "notification_outbox",
        sa.Column("classification_error", sa.String(100), nullable=False, server_default=""),
    )
    op.add_column(
        "notification_outbox", sa.Column("audience", sa.JSON(), nullable=False, server_default="[]")
    )


def downgrade() -> None:
    for column in ("audience", "classification_error", "classification", "classification_status"):
        op.drop_column("notification_outbox", column)
    op.drop_column("push_subscriptions", "group_selection")
    op.drop_column("push_subscriptions", "minimum_interest")
