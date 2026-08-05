"""MFA routes: setup, verify, disable, challenge.

All routes except ``challenge`` require a full (non-partial) JWT.
"""

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routes.auth import create_access_token, get_current_user
from app.utils.rate_limiter import challenge_limiter
from app.utils.tokens import create_partial_token, decode_partial_token

router = APIRouter(prefix="/auth/mfa", tags=["mfa"])


# ── Request / Response models ──────────────────────────────────────────────

class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaVerifyRequest(BaseModel):
    code: str


class MfaDisableRequest(BaseModel):
    password: str


class MfaChallengeRequest(BaseModel):
    partial_token: str
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Helpers ────────────────────────────────────────────────────────────────

def _otpauth_uri(email: str, secret: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name="AUKALABS",
    )


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new TOTP secret and provisioning URI.

    Regenerates the secret on every call. MFA stays disabled until ``verify``
    is called with a valid code.
    """
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = False
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return MfaSetupResponse(secret=secret, provisioning_uri=_otpauth_uri(user.email, secret))


@router.post("/verify")
async def verify_mfa(
    req: MfaVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a TOTP code and enable MFA."""
    if not user.mfa_secret:
        raise HTTPException(status_code=400, detail="Primero debe generar un secreto MFA en /setup")

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(req.code):
        raise HTTPException(status_code=400, detail="Código inválido")

    user.mfa_enabled = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"detail": "MFA activado correctamente"}


@router.post("/disable")
async def disable_mfa(
    req: MfaDisableRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable MFA with password confirmation."""
    from app.routes.auth import pwd_context

    if not user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA no está activado")

    if not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    user.mfa_secret = None
    user.mfa_enabled = False
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"detail": "MFA desactivado correctamente"}


@router.post("/challenge", response_model=TokenResponse)
async def challenge_mfa(
    req: MfaChallengeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a partial token + valid TOTP for a full JWT.

    Rate-limited to 5 attempts per minute per partial token.
    """
    key = req.partial_token
    challenge_limiter.raise_if_limited(key)

    payload = decode_partial_token(req.partial_token)
    user_id = payload.get("sub")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.mfa_secret or not user.mfa_enabled:
        challenge_limiter.record(key)
        raise HTTPException(status_code=401, detail="MFA no configurado")

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(req.code):
        challenge_limiter.record(key)
        raise HTTPException(status_code=401, detail="Código inválido")

    from app.models.tenant import Tenant

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    full_token = create_access_token(
        str(user.id),
        tenant_id=str(tenant.id) if tenant else None,
    )
    return TokenResponse(access_token=full_token)
