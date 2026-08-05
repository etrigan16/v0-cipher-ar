"""Set tenant_id NOT NULL on users table.

Revision ID: 002_tenant_id_not_null
Revises: 001_tenants
Create Date: 2026-08-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_tenant_id_not_null"
down_revision: Union[str, Sequence[str], None] = "001_tenants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set tenant_id NOT NULL on users (all rows already have a value from migration 001)."""
    op.alter_column("users", "tenant_id", nullable=False)


def downgrade() -> None:
    """Revert: make tenant_id nullable again on users."""
    op.alter_column("users", "tenant_id", nullable=True)
