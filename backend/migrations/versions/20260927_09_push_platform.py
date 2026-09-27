"""Record which push service each subscription token belongs to."""

import sqlalchemy as sa
from alembic import op

revision = "20260926_08"
down_revision = "20260924_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Every subscription so far came from the iOS app, so existing rows are APNs tokens.
    op.add_column(
        "push_subscriptions",
        sa.Column("platform", sa.String(length=20), nullable=False, server_default="ios"),
    )


def downgrade() -> None:
    op.drop_column("push_subscriptions", "platform")
