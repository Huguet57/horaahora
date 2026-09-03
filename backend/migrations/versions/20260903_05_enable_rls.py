"""Protect every application table exposed through the Supabase Data API."""

import sqlalchemy as sa
from alembic import op

revision = "20260903_05"
down_revision = "20260722_04"
branch_labels = None
depends_on = None

PUBLIC_TABLES = (
    "agenda_events",
    "agenda_syncs",
    "alembic_version",
    "hour_by_hour_items",
    "notification_deliveries",
    "notification_outbox",
    "notification_sync_state",
    "push_subscriptions",
    "rate_limit_buckets",
)
SUPABASE_API_ROLES = ("anon", "authenticated")


def upgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name != "postgresql":
        return

    existing_api_roles = set(
        connection.scalars(
            sa.text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
        )
    )
    for table in PUBLIC_TABLES:
        op.execute(sa.text(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY'))
        for role in SUPABASE_API_ROLES:
            if role in existing_api_roles:
                op.execute(
                    sa.text(f'REVOKE ALL PRIVILEGES ON TABLE public."{table}" FROM "{role}"')
                )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name != "postgresql":
        return

    existing_api_roles = set(
        connection.scalars(
            sa.text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
        )
    )
    for table in PUBLIC_TABLES:
        op.execute(sa.text(f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY'))
        for role in SUPABASE_API_ROLES:
            if role in existing_api_roles:
                op.execute(sa.text(f'GRANT ALL PRIVILEGES ON TABLE public."{table}" TO "{role}"'))
