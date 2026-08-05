"""FastAPI dependency that extracts tenant_id from JWT and sets DB session context.

On every authenticated request:
1. Decodes the Bearer JWT
2. Extracts ``tenant_id`` (required) and ``sub`` (user_id)
3. Calls ``SET LOCAL app.current_tenant_id`` and ``SET LOCAL app.current_user_id``
   on the DB session so PostgreSQL RLS policies can read them via
   ``current_setting()``
4. Populates ``request.state.current_tenant_id`` for downstream code

If ``tenant_id`` is missing from the JWT, raises 401.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

security = HTTPBearer()


async def get_tenant_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Extract tenant_id from JWT, set DB session context, populate request state.

    Raises 401 if the token is invalid or tenant_id is missing.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    tenant_id = payload.get("tenant_id")
    user_id = payload.get("sub")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin tenant_id",
        )

    # Set PostgreSQL session-local parameters for RLS policies
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
    await db.execute(text(f"SET LOCAL app.current_user_id = '{user_id}'"))

    request.state.current_tenant_id = tenant_id
