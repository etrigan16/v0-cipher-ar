"""Tracking token lookup + campaign-state expiry (design D2).

The public tracking endpoints are token-gated by ``Target.tracking_token``
(design D1) and remain valid only while the campaign's tracking window is
open: ``active`` campaigns resolve forever, ``completed`` campaigns for 7
days past ``completed_at`` (spec R5), and ``draft``/``cancelled`` campaigns
never resolve (cancel stops links immediately, drafts have no tokens).
Unknown tokens and expired campaigns both yield "no context" so routes can
return 404/410 WITHOUT recording an Event (spec R1/R2/R5).

Also hosts the one-way SHA-256 credential hashing (design D4): submitted
credentials are only ever persisted as hashes — the plaintext is discarded
by the route before ``record_event`` runs.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.target import Target

# Tracking links stay valid 7 days after a campaign completes (spec R5).
EXPIRY_DAYS = 7


def sha256_hex(value: str) -> str:
    """Hex SHA-256 of a UTF-8 string — the only form a submitted credential
    ever takes in storage (design D4)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def credential_hash(username: str, password: str) -> str:
    """One-way hash of the submitted pair: ``sha256(f"{username}:{password}")``
    hex (design D4). Plaintext never leaves the request handler."""
    return sha256_hex(f"{username}:{password}")


def is_tracking_expired(campaign: Campaign, *, now: datetime | None = None) -> bool:
    """Return True when a campaign's tracking links must stop resolving (D2).

    - ``active`` → never expired (links live while the campaign runs)
    - ``completed`` → expired 7 days past ``completed_at`` (spec R5)
    - ``draft`` / ``cancelled`` / anything else → expired

    SQLite returns naive datetimes for ``DateTime(timezone=True)`` columns;
    normalize both sides to UTC so the comparison is well-defined.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if campaign.status == "active":
        return False
    if campaign.status == "completed" and campaign.completed_at is not None:
        completed = campaign.completed_at
        if completed.tzinfo is None:
            completed = completed.replace(tzinfo=timezone.utc)
        return now > completed + timedelta(days=EXPIRY_DAYS)
    return True


async def resolve_tracking_target(
    db: AsyncSession, token: str, *, now: datetime | None = None
) -> tuple[Target, Campaign, bool] | None:
    """Look up ``(Target, Campaign, expired)`` by public tracking token.

    Returns ``None`` for an UNKNOWN token; for a known token returns the
    target, its campaign and whether the tracking window has closed (D2).
    Callers must not record an Event when the result is ``None`` or
    ``expired`` is True (spec R1/R2/R3/R5).
    """
    result = await db.execute(select(Target).where(Target.tracking_token == token))
    target = result.scalar_one_or_none()
    if target is None:
        return None
    campaign = await db.get(Campaign, target.campaign_id)
    if campaign is None:
        return target, None, True  # orphaned row — treat as expired
    return target, campaign, is_tracking_expired(campaign, now=now)
