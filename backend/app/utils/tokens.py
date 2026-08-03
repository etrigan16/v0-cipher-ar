"""Partial token creation and validation for MFA two-step login.

A partial token is a short-lived JWT (5 min) with an ``mfa_challenge: true``
claim.  ``get_current_user`` rejects any token carrying that claim.

Full token and partial token use the same secret/algorithm so only one decode
path is needed in ``get_current_user``.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

PARTIAL_TOKEN_EXPIRE_MINUTES = 5

security = HTTPBearer()


def create_partial_token(user_id: str) -> str:
    """Return a 5-minute JWT with ``mfa_challenge: true``."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=PARTIAL_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "mfa_challenge": True},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_partial_token(token: str) -> dict:
    """Decode and validate a partial token.  Returns the payload on success.

    Raises 401 on any decode error (expired, invalid signature, etc.).
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token parcial inválido o expirado",
        )
    return payload


def reject_partial_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """Dependency guard that raises 401 if the bearer token is a partial token.

    Place this AFTER ``get_current_user`` in routes that should never receive
    an MFA-challenge token (all existing routes).
    """
    # No need to decode again — ``get_current_user`` already did.
    # This is called separately only when the token wasn't decoded yet.
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        return  # Let get_current_user handle invalid tokens.

    if payload.get("mfa_challenge"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA challenge required",
        )
