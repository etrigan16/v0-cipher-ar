import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
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


class Asset(Base):
    """A discovered entity in a tenant's external attack surface.

    Composite unique ``(tenant_id, domain, subdomain)`` prevents duplicate
    rows on re-scan; re-scans upsert (preserve ``first_seen``, bump
    ``last_seen``) via the discovery orchestrator.
    """

    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "domain", "subdomain", name="uq_assets_tenant_domain_subdomain"
        ),
        Index("ix_assets_tenant_id", "tenant_id"),
    )

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=False)
    domain = Column(String, nullable=False)
    subdomain = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    service = Column(String, nullable=True)
    fingerprint = Column(Text, nullable=True)  # JSON-encoded fingerprint dict
    status = Column(String, nullable=False, default="discovered")
    # Tenant-level risk aggregate (max of open findings' risk_score, migration 004).
    risk_score = Column(Float, nullable=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
