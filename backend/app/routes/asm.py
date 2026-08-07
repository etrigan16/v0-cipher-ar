"""Attack-surface API — Phase 3 Orchestration + API.

Real, auth-protected handlers wiring the discovery orchestrator into the
``Asset``/``Scan``/``Finding`` tables. Multi-tenant isolation is enforced at
the app level by filtering every query on the authenticated user's
``tenant_id`` (RLS is PostgreSQL-only, so this app filter is what proves
isolation on SQLite). A cross-tenant scan id yields 404 and no data leaks.
"""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.user import User
from app.routes.auth import get_current_user
from app.services.orchestrator import run_scan

router = APIRouter(prefix="/asm", tags=["asm"])


class ScanCreate(BaseModel):
    domain: str


class AssetDTO(BaseModel):
    id: str
    domain: str
    subdomain: str | None
    ip: str | None
    port: int | None
    service: str | None
    fingerprint: dict | None
    status: str
    first_seen: datetime
    last_seen: datetime


class ScanDTO(BaseModel):
    id: str
    domain: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class FindingDTO(BaseModel):
    id: str
    asset_id: str
    severity: str
    title: str
    detail: str | None
    discovered_at: datetime


def _asset_dto(a: Asset) -> AssetDTO:
    fingerprint = None
    if a.fingerprint:
        try:
            fingerprint = json.loads(a.fingerprint)
        except (json.JSONDecodeError, TypeError):
            fingerprint = None
    return AssetDTO(
        id=str(a.id),
        domain=a.domain,
        subdomain=a.subdomain,
        ip=a.ip,
        port=a.port,
        service=a.service,
        fingerprint=fingerprint,
        status=a.status,
        first_seen=a.first_seen,
        last_seen=a.last_seen,
    )


def _scan_dto(s: Scan) -> ScanDTO:
    return ScanDTO(
        id=str(s.id),
        domain=s.domain,
        status=s.status,
        started_at=s.started_at,
        completed_at=s.completed_at,
        created_at=s.created_at,
    )


def _finding_dto(f: Finding) -> FindingDTO:
    return FindingDTO(
        id=str(f.id),
        asset_id=str(f.asset_id),
        severity=f.severity,
        title=f.title,
        detail=f.detail,
        discovered_at=f.discovered_at,
    )


@router.post("/scans", status_code=status.HTTP_201_CREATED)
async def trigger_scan(
    body: ScanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run passive + active discovery synchronously and persist assets/findings."""
    domain = body.domain.strip().lower()
    scan = await run_scan(db, tenant_id=user.tenant_id, domain=domain)

    result = await db.execute(
        select(Asset).where(
            Asset.tenant_id == user.tenant_id,
            Asset.domain == domain,
        )
    )
    assets = result.scalars().all()

    return {
        "scan": _scan_dto(scan),
        "assets": [_asset_dto(a) for a in assets],
    }


@router.get("/assets")
async def list_assets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List only the current tenant's assets (app-level isolation)."""
    result = await db.execute(
        select(Asset)
        .where(Asset.tenant_id == user.tenant_id)
        .order_by(Asset.last_seen.desc())
    )
    return {"assets": [_asset_dto(a) for a in result.scalars().all()]}


@router.get("/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return tenant-scoped counts for the dashboard stat cards.

    Each count is filtered on the authenticated user's ``tenant_id`` so a
    tenant only ever sees its own data (same app-level isolation as the
    other /asm routes).
    """
    assets = await db.scalar(
        select(func.count())
        .select_from(Asset)
        .where(Asset.tenant_id == user.tenant_id)
    )
    findings = await db.scalar(
        select(func.count())
        .select_from(Finding)
        .where(Finding.tenant_id == user.tenant_id)
    )
    scans = await db.scalar(
        select(func.count())
        .select_from(Scan)
        .where(Scan.tenant_id == user.tenant_id)
    )
    return {
        "assets": assets or 0,
        "findings": findings or 0,
        "scans": scans or 0,
    }


@router.get("/results/{scan_id}")
async def get_results(
    scan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a scan and its findings, scoped to the tenant (cross-tenant = 404)."""
    scan_result = await db.execute(
        select(Scan).where(
            Scan.id == scan_id,
            Scan.tenant_id == user.tenant_id,
        )
    )
    scan = scan_result.scalar_one_or_none()
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    findings_result = await db.execute(
        select(Finding).where(
            Finding.scan_id == scan.id,
            Finding.tenant_id == user.tenant_id,
        )
    )

    return {
        "scan": _scan_dto(scan),
        "findings": [_finding_dto(f) for f in findings_result.scalars().all()],
    }
