import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
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


class Template(Base):
    """A phishing email template.

    ``tenant_id`` is NULLABLE: NULL rows are the 8 shared seed templates
    (migration 005) that every tenant can use (D9 — RLS policy exposes
    ``tenant_id IS NULL`` rows). Categories: ``bank|government|tech``.
    """

    __tablename__ = "templates"
    __table_args__ = (
        Index("ix_templates_tenant_id", "tenant_id"),
    )

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    html_body = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # bank|government|tech
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
