import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
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


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    company = Column(String, nullable=True)
    source = Column(String, nullable=False, default="landing")
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
