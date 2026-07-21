"""Create the provider-neutral agenda cache and synchronization metadata."""

from alembic import op
import sqlalchemy as sa


revision = "20260721_02"
down_revision = "20260720_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_table("agenda_syncs")
    op.drop_table("agenda_events")
