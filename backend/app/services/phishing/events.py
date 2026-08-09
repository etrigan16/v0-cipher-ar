"""Tracking Event recording helper (design D3).

Every access on the public tracking endpoints (open/click/landing/credential/
report) is persisted as an ``Event`` row with ``campaign_id``, ``target_id``,
``type``, a JSON ``metadata`` payload (ip, user_agent, url, hash — spec R5)
and an ``occurred_at`` timestamp. The ``(campaign_id, type)`` index supports
per-type results aggregation (Phase 5).

Credential events only ever receive SHA-256 hashes (design D4): the route
discards the plaintext before calling this helper, so no plaintext can reach
the database.
"""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


async def record_event(
    db: AsyncSession,
    *,
    tenant_id,
    campaign_id,
    target_id,
    type: str,
    metadata: dict | None = None,
) -> Event:
    """Persist one tracking ``Event`` row and return it.

    ``metadata`` is stored as a JSON-encoded Text value (spec R5: ip,
    user_agent, url, hash). Commits immediately so the audit row is durable
    before the HTTP response returns.
    """
    event = Event(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        target_id=target_id,
        type=type,
        metadata_=json.dumps(metadata, ensure_ascii=False) if metadata else None,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
