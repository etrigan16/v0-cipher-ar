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


class Finding(Base):
    """An issue detected on an asset during a scan."""

    __tablename__ = "findings"
    __table_args__ = (
        Index("ix_findings_tenant_id", "tenant_id"),
    )

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=False)
    asset_id = Column(CoercingUuid(), ForeignKey("assets.id"), nullable=False)
    scan_id = Column(CoercingUuid(), ForeignKey("scans.id"), nullable=False)
    severity = Column(String, nullable=False, default="info")  # info|low|medium|high|critical
    title = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
