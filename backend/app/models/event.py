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


class Event(Base):
    """An audit record of a tracking access on a campaign target.

    ``type`` is one of ``open|click|report|credential|landing`` (design D3;
    the tracking spec core set is ``open|click|report|credential``).
    ``metadata`` is a JSON-encoded Text dict (ip, user_agent, url, hash) —
    for credentials only the SHA-256 hash is ever stored (D4).
    """

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_tenant_id", "tenant_id"),
        Index("ix_events_campaign_type", "campaign_id", "type"),
    )

    id = Column(CoercingUuid(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(CoercingUuid(), ForeignKey("tenants.id"), nullable=False)
    campaign_id = Column(CoercingUuid(), ForeignKey("campaigns.id"), nullable=False)
    target_id = Column(CoercingUuid(), ForeignKey("targets.id"), nullable=False)
    type = Column(String, nullable=False)
    # `metadata` is reserved by the declarative API; keep the DB column name
    # from the design and expose the ORM attribute as `metadata_`.
    metadata_ = Column("metadata", Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
