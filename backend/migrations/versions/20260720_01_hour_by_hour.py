"""Create the provider-neutral Hour by Hour cache."""

import sqlalchemy as sa
from alembic import op

revision = "20260720_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
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
        sa.UniqueConstraint("source_id", "external_id", name="uq_hour_by_hour_source_external"),
    )
    op.create_index("ix_hour_by_hour_items_source_id", "hour_by_hour_items", ["source_id"])
    op.create_index("ix_hour_by_hour_items_published_at", "hour_by_hour_items", ["published_at"])
    op.create_index("ix_hour_by_hour_items_updated_at", "hour_by_hour_items", ["updated_at"])


def downgrade() -> None:
    op.drop_table("hour_by_hour_items")
