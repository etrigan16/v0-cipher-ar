"""Create phishing tables (templates, campaigns, targets, events) + 8 seeds.

Revision ID: 005_phishing
Revises: 004_risk_scoring
Create Date: 2026-08-09

Additive migration: creates four NEW tenant-scoped tables (no changes to
existing rows/columns). Each table gets an ``ix_*_tenant_id`` index;
``targets`` additionally enforces uniqueness on ``(tenant_id, campaign_id,
email)`` and a unique index on ``tracking_token`` (the public token-gated
lookup key); ``events`` gets a composite ``(campaign_id, type)`` index for
results aggregation.

Seeds: 8 templates with ``tenant_id NULL`` (3 bank / 3 government / 2 tech),
each carrying the ``{{nombre}}``, ``{{empresa}}`` and ``{{link}}`` variables.
NULL-tenant rows are visible to every tenant via the ``OR tenant_id IS NULL``
RLS policy (design D9).

Rollback: ``downgrade()`` drops the four tables; seeds disappear with
``templates``.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_phishing"
down_revision: Union[str, Sequence[str], None] = "004_risk_scoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the four phishing tables with FKs, indexes and the 8 seeds."""
    op.create_table(
        "templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_templates_tenant_id", "templates", ["tenant_id"])

    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("template_id", sa.Uuid(), sa.ForeignKey("templates.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_campaigns_tenant_id", "campaigns", ["tenant_id"])

    op.create_table(
        "targets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("tracking_token", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "tenant_id", "campaign_id", "email", name="uq_targets_tenant_campaign_email"
        ),
    )
    op.create_index("ix_targets_tenant_id", "targets", ["tenant_id"])
    op.create_index("ix_targets_campaign_id", "targets", ["campaign_id"])
    op.create_index(
        "ix_targets_tracking_token", "targets", ["tracking_token"], unique=True
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("target_id", sa.Uuid(), sa.ForeignKey("targets.id"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("metadata", sa.Text(), nullable=True),  # JSON dict: ip, user_agent, url, hash
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_events_tenant_id", "events", ["tenant_id"])
    op.create_index("ix_events_campaign_type", "events", ["campaign_id", "type"])

    # 8 shared seed templates (tenant_id NULL, visible to every tenant — D9).
    # UUIDs are explicit so seeds are deterministic across environments.
    templates = sa.table(
        "templates",
        sa.column("id", sa.Uuid()),
        sa.column("tenant_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("subject", sa.String()),
        sa.column("html_body", sa.Text()),
        sa.column("category", sa.String()),
    )
    op.bulk_insert(
        templates,
        [
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000001"),
                "tenant_id": None,
                "name": "Alerta de actividad inusual",
                "subject": "Aviso de seguridad para {{nombre}} en {{empresa}}",
                "html_body": (
                    "<p>Hola {{nombre}}, detectamos actividad inusual en tu cuenta "
                    "de {{empresa}}.</p><p><a href=\"{{link}}\">Verifica tu "
                    "actividad aqui</a></p>"
                ),
                "category": "bank",
            },
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000002"),
                "tenant_id": None,
                "name": "Verificacion de cuenta",
                "subject": "Verificacion de cuenta {{empresa}}",
                "html_body": (
                    "<p>{{nombre}}, confirma tus datos en {{empresa}} antes de 24 "
                    "horas.</p><p><a href=\"{{link}}\">Confirmar</a></p>"
                ),
                "category": "bank",
            },
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000003"),
                "tenant_id": None,
                "name": "Bloqueo temporal de acceso",
                "subject": "Acceso bloqueado: {{empresa}}",
                "html_body": (
                    "<p>Hola {{nombre}}, tu acceso a {{empresa}} fue bloqueado."
                    "</p><p><a href=\"{{link}}\">Restablecer acceso</a></p>"
                ),
                "category": "bank",
            },
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000004"),
                "tenant_id": None,
                "name": "Devolucion de impuestos",
                "subject": "Devolucion de impuestos disponible",
                "html_body": (
                    "<p>{{nombre}}, tienes una devolucion pendiente en {{empresa}}."
                    "</p><p><a href=\"{{link}}\">Solicitar devolucion</a></p>"
                ),
                "category": "government",
            },
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000005"),
                "tenant_id": None,
                "name": "Actualizacion de datos fiscales",
                "subject": "Actualiza tus datos fiscales",
                "html_body": (
                    "<p>{{nombre}}, {{empresa}} actualizo sus requisitos "
                    "fiscales.</p><p><a href=\"{{link}}\">Actualizar</a></p>"
                ),
                "category": "government",
            },
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000006"),
                "tenant_id": None,
                "name": "Multa de transito pendiente",
                "subject": "Multa de transito pendiente",
                "html_body": (
                    "<p>Hola {{nombre}}, registramos una infraccion a nombre de "
                    "{{empresa}}.</p><p><a href=\"{{link}}\">Ver detalle</a></p>"
                ),
                "category": "government",
            },
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000007"),
                "tenant_id": None,
                "name": "Restablecimiento de contrasena",
                "subject": "Restablece tu contrasena de {{empresa}}",
                "html_body": (
                    "<p>{{nombre}}, alguien solicito restablecer tu contrasena de "
                    "{{empresa}}.</p><p><a href=\"{{link}}\">Cambiar contrasena</a></p>"
                ),
                "category": "tech",
            },
            {
                "id": uuid.UUID("50000000-0000-0000-0000-000000000008"),
                "tenant_id": None,
                "name": "Alerta de inicio de sesion",
                "subject": "Nuevo inicio de sesion en {{empresa}}",
                "html_body": (
                    "<p>Hola {{nombre}}, se registro un inicio de sesion en tu "
                    "cuenta de {{empresa}}.</p><p><a href=\"{{link}}\">Revisar "
                    "actividad</a></p>"
                ),
                "category": "tech",
            },
        ],
    )


def downgrade() -> None:
    """Drop the four phishing tables (seeds disappear with templates)."""
    op.drop_table("events")
    op.drop_table("targets")
    op.drop_table("campaigns")
    op.drop_table("templates")
