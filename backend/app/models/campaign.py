import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
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


class Campaign(Base):
    """A tenant-owned phishing campaign built from a template.

    ``status`` lifecycle: ``draft`` → ``active`` (launch) → ``completed`` or
    ``cancelled``. ``started_at``/``completed_at`` are set by launch/cancel;
    tracking tokens expire 7 days after ``completed_at`` (tracking spec R5).
    """

    __tablename__ = "campaigns"
    __table_args__ = (
        Index("ix_campaigns_tenant_id", "tenant_id"),
    )

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    template_id = Column(CoercingUuid(), ForeignKey("templates.id"), nullable=False)
    status = Column(String, nullable=False, default="draft", server_default="draft")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
