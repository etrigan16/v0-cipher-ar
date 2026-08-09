import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy import Uuid as SqlUuid
from sqlalchemy.sql import func

from app.database import Base


class CoercingUuid(SqlUuid):
    """Portable ``sqlalchemy.Uuid`` that also coerces string binds.

    SQLAlchemy 2.0.36's ``Uuid`` bind processor calls ``value.hex`` and
    rejects plain strings on character-based dialects (SQLite). Coerce
    strings to ``uuid.UUID`` before delegating to the dialect processor.
    """

    def bind_processor(self, dialect):
        process = super().bind_processor(dialect)
        if process is None:
            return None

        def coerce(value):
            if isinstance(value, str):
                value = uuid.UUID(value)
            return process(value)

        return coerce


class Target(Base):
    """A single recipient of a campaign.

    ``tracking_token`` (``secrets.token_urlsafe(16)`` at launch) is unique
    across ALL campaigns — it is the public, token-gated lookup key for
    tracking endpoints. ``(tenant_id, campaign_id, email)`` is unique so a
    CSV upload cannot create duplicate targets inside one campaign.
    """

    __tablename__ = "targets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "campaign_id", "email", name="uq_targets_tenant_campaign_email"
        ),
        Index("ix_targets_tenant_id", "tenant_id"),
        Index("ix_targets_campaign_id", "campaign_id"),
        Index("ix_targets_tracking_token", "tracking_token", unique=True),
    )

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=False)
    campaign_id = Column(CoercingUuid(), ForeignKey("campaigns.id"), nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", server_default="pending")
    tracking_token = Column(String, nullable=True)  # assigned at launch (R4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
