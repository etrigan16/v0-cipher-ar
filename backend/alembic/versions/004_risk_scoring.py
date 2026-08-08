"""Additive risk-scoring columns to findings/assets.

Revision ID: 004_risk_scoring
Revises: 003_attack_surface
Create Date: 2026-08-08

All columns are nullable EXCEPT ``findings.status`` (NOT NULL, server default
``'open'``). This is a pure additive migration: existing rows are untouched;
legacy rows read back with NULL risk/enrichment fields and ``status='open'``
until the next scan recomputes them (spec: no backfill).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_risk_scoring"
down_revision: Union[str, Sequence[str], None] = "003_attack_surface"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the risk/enrichment/status columns to ``findings`` and ``assets``."""
    # Findings: per-finding risk score + level, rule finding_type, remediation,
    # LLM enrichment fields (context, llm_summary, enriched_at) and status.
    op.add_column("findings", sa.Column("risk_score", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("risk_level", sa.String(), nullable=True))
    op.add_column("findings", sa.Column("finding_type", sa.String(), nullable=True))
    op.add_column("findings", sa.Column("remediation", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("context", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("llm_summary", sa.Text(), nullable=True))
    op.add_column(
        "findings",
        sa.Column("enriched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "findings",
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
    )

    # Assets: tenant-level risk aggregate (max of open findings' risk_score).
    op.add_column("assets", sa.Column("risk_score", sa.Float(), nullable=True))


def downgrade() -> None:
    """Drop only the columns added above; prior data remains."""
    op.drop_column("assets", "risk_score")
    op.drop_column("findings", "status")
    op.drop_column("findings", "enriched_at")
    op.drop_column("findings", "llm_summary")
    op.drop_column("findings", "context")
    op.drop_column("findings", "remediation")
    op.drop_column("findings", "finding_type")
    op.drop_column("findings", "risk_level")
    op.drop_column("findings", "risk_score")
