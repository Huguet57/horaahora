"""Keep calculator conversations the app shares to improve the product."""

import sqlalchemy as sa
from alembic import op

revision = "20260927_08"
down_revision = "20260924_07"
branch_labels = None
depends_on = None

SUPABASE_API_ROLES = ("anon", "authenticated")


def upgrade() -> None:
    # No installation identifier or IP address: rows cannot be linked to a device.
    op.create_table(
        "shared_conversations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("messages", sa.JSON(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_shared_conversations_conversation_id", "shared_conversations", ["conversation_id"]
    )
    op.create_index("ix_shared_conversations_created_at", "shared_conversations", ["created_at"])

    connection = op.get_bind()
    if connection.dialect.name != "postgresql":
        return
    op.execute(sa.text('ALTER TABLE public."shared_conversations" ENABLE ROW LEVEL SECURITY'))
    existing_api_roles = set(
        connection.scalars(
            sa.text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
        )
    )
    for role in SUPABASE_API_ROLES:
        if role in existing_api_roles:
            op.execute(
                sa.text(
                    f'REVOKE ALL PRIVILEGES ON TABLE public."shared_conversations" FROM "{role}"'
                )
            )


def downgrade() -> None:
    op.drop_index("ix_shared_conversations_created_at", table_name="shared_conversations")
    op.drop_index("ix_shared_conversations_conversation_id", table_name="shared_conversations")
    op.drop_table("shared_conversations")
