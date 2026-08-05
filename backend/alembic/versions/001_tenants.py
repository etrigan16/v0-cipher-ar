"""Create tenants table, add tenant_id + is_superadmin, seed default tenant.

Revision ID: 001_tenants
Revises: None
Create Date: 2026-08-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_tenants"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tenants table, add FK columns, seed default tenant."""

    # 1. Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"])

    # 2. Add is_superadmin to users
    op.add_column(
        "users",
        sa.Column("is_superadmin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # 3. Add tenant_id to users (nullable initially)
    op.add_column(
        "users",
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_tenant_id",
        "users",
        "tenants",
        ["tenant_id"],
        ["id"],
    )

    # 4. Add tenant_id to waitlist_entries (nullable)
    op.add_column(
        "waitlist_entries",
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_waitlist_entries_tenant_id",
        "waitlist_entries",
        "tenants",
        ["tenant_id"],
        ["id"],
    )

    # 5. Seed default "AUKALABS" tenant
    op.execute(
        "INSERT INTO tenants (name, slug) VALUES ('AUKALABS', 'aukalabs')"
    )

    # 6. Assign existing users to default tenant
    op.execute(
        "UPDATE users SET tenant_id = (SELECT id FROM tenants WHERE slug = 'aukalabs')"
    )

    # 7. Assign existing waitlist entries to default tenant
    op.execute(
        "UPDATE waitlist_entries SET tenant_id = (SELECT id FROM tenants WHERE slug = 'aukalabs')"
    )


def downgrade() -> None:
    """Revert migration: drop FK columns and tenants table."""
    # Drop foreign keys first
    op.drop_constraint("fk_waitlist_entries_tenant_id", "waitlist_entries", type_="foreignkey")
    op.drop_column("waitlist_entries", "tenant_id")

    op.drop_constraint("fk_users_tenant_id", "users", type_="foreignkey")
    op.drop_column("users", "tenant_id")
    op.drop_column("users", "is_superadmin")

    op.drop_index(op.f("ix_tenants_slug"), table_name="tenants")
    op.drop_table("tenants")
