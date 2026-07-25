"""Store the source-provided title and the app display title separately."""

import sqlalchemy as sa
from alembic import op

revision = "20260721_03"
down_revision = "20260721_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("hour_by_hour_items") as batch_op:
        batch_op.add_column(sa.Column("display_title", sa.Text(), nullable=True))

    op.execute(
        sa.text("UPDATE hour_by_hour_items SET display_title = title WHERE display_title IS NULL")
    )

    with op.batch_alter_table("hour_by_hour_items") as batch_op:
        batch_op.alter_column("display_title", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("hour_by_hour_items") as batch_op:
        batch_op.drop_column("display_title")
