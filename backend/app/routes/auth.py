from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from slugify import slugify

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TenantResponse(BaseModel):
    id: str
    slug: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    tenant: TenantResponse | None = None


def create_access_token(user_id: str, tenant_id: str | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    # Auto-generate slug from company name
    tenant_slug = slugify(req.company_name)

    # Create Tenant + User in a single transaction
    tenant = Tenant(name=req.company_name, slug=tenant_slug)
    db.add(tenant)
    await db.flush()  # Flush to get tenant.id without committing

    user = User(
        email=req.email,
        name=req.name,
        hashed_password=pwd_context.hash(req.password),
        tenant_id=tenant.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(tenant)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        tenant=TenantResponse(id=str(tenant.id), slug=tenant.slug),
    )


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Load tenant for token
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    token = create_access_token(
        str(user.id),
        tenant_id=str(tenant.id) if tenant else None,
    )
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        tenant=TenantResponse(id=str(tenant.id), slug=tenant.slug) if tenant else None,
    )
