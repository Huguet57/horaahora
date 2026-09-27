"""Track popular public social posts and their Hora a Hora headline decisions."""

import sqlalchemy as sa
from alembic import op

revision = "20260927_09"
down_revision = "20260927_08"
branch_labels = None
depends_on = None

SUPABASE_API_ROLES = ("anon", "authenticated")


def upgrade() -> None:
    op.create_table(
        "social_posts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("network", sa.String(length=20), nullable=False),
        sa.Column("post_id", sa.String(length=64), nullable=False),
        sa.Column("author_id", sa.String(length=64), nullable=False),
        sa.Column("author_username", sa.String(length=64), nullable=False),
        sa.Column("author_name", sa.String(length=200), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("error", sa.String(length=100), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("network", "post_id", name="uq_social_posts_network_post"),
    )
    op.create_index("ix_social_posts_published_at", "social_posts", ["published_at"])
    op.create_index("ix_social_posts_status", "social_posts", ["status"])

    # Like every application table, keep it out of the Supabase Data API.
    connection = op.get_bind()
    if connection.dialect.name != "postgresql":
        return
    op.execute(sa.text('ALTER TABLE public."social_posts" ENABLE ROW LEVEL SECURITY'))
    existing_api_roles = set(
        connection.scalars(
            sa.text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
        )
    )
    for role in SUPABASE_API_ROLES:
        if role in existing_api_roles:
            op.execute(
                sa.text(f'REVOKE ALL PRIVILEGES ON TABLE public."social_posts" FROM "{role}"')
            )


def downgrade() -> None:
    op.drop_index("ix_social_posts_status", table_name="social_posts")
    op.drop_index("ix_social_posts_published_at", table_name="social_posts")
    op.drop_table("social_posts")
