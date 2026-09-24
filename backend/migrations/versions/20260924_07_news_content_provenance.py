"""Freeze the article reference separately from the notification's destination URL."""

import sqlalchemy as sa
from alembic import op

revision = "20260924_07"
down_revision = "20260924_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Unknown references remain empty: do not infer historical provenance from
    # mutable feed rows or reclassify any previously processed notification.
    op.add_column(
        "notification_outbox",
        sa.Column("article_url", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("notification_outbox", "article_url")
