from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes import auth, asm, phishing, waitlist, mfa
from app.database import async_session, init_db

app = FastAPI(title="Aukalabs API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://aukalabs.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(asm.router)
app.include_router(phishing.router)
app.include_router(waitlist.router)
app.include_router(mfa.router)


async def seed_default_tenant():
    """Ensure the default 'AUKALABS' tenant exists and assign orphan rows.

    Covers fresh deployments where Alembic hasn't run the seed migration.
    """
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.waitlist import WaitlistEntry

    async with async_session() as session:
        # Check if default tenant exists
        result = await session.execute(
            select(Tenant).where(Tenant.slug == "aukalabs")
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(name="AUKALABS", slug="aukalabs")
            session.add(tenant)
            await session.flush()

        # Assign any users with NULL tenant_id
        await session.execute(
            text(
                "UPDATE users SET tenant_id = :tid WHERE tenant_id IS NULL"
            ).bindparams(tid=tenant.id)
        )

        # Assign any waitlist entries with NULL tenant_id
        await session.execute(
            text(
                "UPDATE waitlist_entries SET tenant_id = :tid WHERE tenant_id IS NULL"
            ).bindparams(tid=tenant.id)
        )

        await session.commit()


@app.on_event("startup")
async def startup():
    await init_db()
    await seed_default_tenant()


@app.get("/health")
async def health():
    return {"status": "ok"}
