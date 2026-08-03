import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy import Uuid as SqlUuid
from sqlalchemy.sql import func

from app.database import Base


class CoercingUuid(SqlUuid):
    """Portable ``sqlalchemy.Uuid`` that also coerces string binds.

    SQLAlchemy 2.0.36's ``Uuid`` bind processor calls ``value.hex`` and
    rejects plain strings on character-based dialects (SQLite). JWT subjects
    (``sub``) arrive as strings, so coerce them to ``uuid.UUID`` before
    delegating to the dialect processor. Native UUID stays in use on
    PostgreSQL; SQLite stores CHAR(32).
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


class User(Base):
    __tablename__ = "users"

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
