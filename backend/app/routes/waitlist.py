import logging
from datetime import datetime, timezone
from typing import Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.waitlist import WaitlistEntry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/waitlist", tags=["waitlist"])

# In-memory cooldown: email -> last submission UNIX timestamp
_cooldown: Dict[str, float] = {}
COOLDOWN_SECONDS = 300  # 5 minutes


class WaitlistCreate(BaseModel):
    email: EmailStr
    company: str | None = None


class WaitlistResponse(BaseModel):
    id: str
    email: str
    company: str | None
    created_at: datetime


async def send_confirmation_email(user_email: str) -> None:
    """Fire-and-forget: send a confirmation email via Resend. Never raises."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": "onboarding@aukalabs.com",
                    "to": user_email,
                    "subject": "¡Gracias por sumarte a AUKALABS!",
                    "html": """<!DOCTYPE html>
<html>
<body style="font-family:sans-serif; background:#000; color:#fff; padding:20px;">
  <h2 style="color:#00ff99;">Thanks for joining the waitlist!</h2>
  <p style="color:#ccc;">
    We'll keep you posted on Aukalabs launches and updates.
  </p>
  <p style="color:#666;">&mdash; The Aukalabs Team</p>
</body>
</html>""",
                },
            )
            if not resp.is_success:
                logger.warning(
                    "Resend API returned %s: %s", resp.status_code, resp.text
                )
    except Exception as exc:
        logger.warning(
            "Failed to send confirmation email to %s: %s", user_email, exc
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_waitlist_entry(
    body: WaitlistCreate,
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc).timestamp()

    # Rate limit check
    last_attempt = _cooldown.get(body.email)
    if last_attempt is not None and (now - last_attempt) < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - last_attempt))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Try again later",
            headers={"retry-after": str(remaining)},
        )

    # Duplicate check
    result = await db.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == body.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create entry
    entry = WaitlistEntry(email=body.email, company=body.company)
    db.add(entry)
    try:
        await db.commit()
        await db.refresh(entry)
    except Exception:
        await db.rollback()
        logger.exception("Database error creating waitlist entry")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    # Update cooldown after successful insert
    _cooldown[body.email] = now

    # Fire-and-forget confirmation email (never fails the request)
    try:
        await send_confirmation_email(body.email)
    except Exception:
        logger.exception("Failed to send confirmation email (fire-and-forget)")

    return WaitlistResponse(
        id=str(entry.id),
        email=entry.email,
        company=entry.company,
        created_at=entry.created_at,
    )
