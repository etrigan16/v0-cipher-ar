"""Attack-surface API — Phase 3 Orchestration + API.

Real, auth-protected handlers wiring the discovery orchestrator into the
``Asset``/``Scan``/``Finding`` tables. Multi-tenant isolation is enforced at
the app level by filtering every query on the authenticated user's
``tenant_id`` (RLS is PostgreSQL-only, so this app filter is what proves
isolation on SQLite). A cross-tenant scan id yields 404 and no data leaks.
"""

import json
import uuid
from datetime import datetime
from typing import Literal

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
from app.services.orchestrator import recompute_asset_risk, run_scan

router = APIRouter(prefix="/asm", tags=["asm"])

# Severity bands — the fixed key set for ``severity_counts`` in risk summaries.
SEVERITIES = ("info", "low", "medium", "high", "critical")


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
    risk_score: float | None = None
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
    risk_score: float | None = None
    risk_level: str | None = None
    finding_type: str | None = None
    remediation: str | None = None
    status: str = "open"
    enriched_at: datetime | None = None
    discovered_at: datetime


def _coerce_uuid(value: str) -> uuid.UUID | None:
    """Return the UUID when ``value`` parses, else ``None`` (invalid input).

    Query/filter values that are not valid UUIDs must not raise a 500 in the
    ``CoercingUuid`` bind processor; callers treat ``None`` as \"no match\".
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


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
        risk_score=a.risk_score,
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
        risk_score=f.risk_score,
        risk_level=f.risk_level,
        finding_type=f.finding_type,
        remediation=f.remediation,
        status=f.status,
        enriched_at=f.enriched_at,
        discovered_at=f.discovered_at,
    )


async def _severity_counts(db: AsyncSession, tenant_id) -> dict[str, int]:
    """Count findings per severity band, always with the full 5-key shape."""
    result = await db.execute(
        select(Finding.severity, func.count())
        .where(Finding.tenant_id == tenant_id)
        .group_by(Finding.severity)
    )
    counts = {severity: 0 for severity in SEVERITIES}
    for severity, count in result.all():
        if severity in counts:
            counts[severity] = count
    return counts


async def _risk_metrics(db: AsyncSession, tenant_id) -> dict:
    """Tenant-scoped risk overview shared by risk-summary and stats.

    Returns severity distribution, average/max ``risk_score`` over the
    tenant's scored findings (0.0 when none) and the open-finding count.
    """
    avg_risk = await db.scalar(
        select(func.avg(Finding.risk_score)).where(
            Finding.tenant_id == tenant_id,
            Finding.risk_score.is_not(None),
        )
    )
    max_risk = await db.scalar(
        select(func.max(Finding.risk_score)).where(
            Finding.tenant_id == tenant_id,
            Finding.risk_score.is_not(None),
        )
    )
    open_findings = await db.scalar(
        select(func.count())
        .select_from(Finding)
        .where(Finding.tenant_id == tenant_id, Finding.status == "open")
    )
    return {
        "severity_counts": await _severity_counts(db, tenant_id),
        "avg_risk": round(float(avg_risk), 2) if avg_risk is not None else 0.0,
        "max_risk": round(float(max_risk), 2) if max_risk is not None else 0.0,
        "open_findings": open_findings or 0,
    }


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


@router.get("/findings")
async def list_findings(
    severity: str | None = None,
    status: str | None = None,
    asset_id: str | None = None,
    scan_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the tenant's findings, filtered, sorted by ``risk_score`` desc.

    Filters mirror spec R4 (severity/status/asset_id/scan_id) plus
    ``limit``/``offset`` pagination. Sorting uses ``NULLS LAST`` so legacy
    unscored findings (``risk_score IS NULL``) trail scored ones. Cross-tenant
    rows are excluded by the ``tenant_id`` filter; an invalid UUID filter
    value matches nothing instead of raising.
    """
    conditions = [Finding.tenant_id == user.tenant_id]
    if severity:
        conditions.append(Finding.severity == severity)
    if status:
        conditions.append(Finding.status == status)
    if asset_id:
        parsed = _coerce_uuid(asset_id)
        if parsed is None:
            return {"findings": [], "total": 0, "limit": limit, "offset": offset}
        conditions.append(Finding.asset_id == parsed)
    if scan_id:
        parsed = _coerce_uuid(scan_id)
        if parsed is None:
            return {"findings": [], "total": 0, "limit": limit, "offset": offset}
        conditions.append(Finding.scan_id == parsed)

    total = await db.scalar(
        select(func.count()).select_from(Finding).where(*conditions)
    )
    result = await db.execute(
        select(Finding)
        .where(*conditions)
        .order_by(
            Finding.risk_score.desc().nullslast(),
            Finding.title.asc(),  # deterministic tie-break for equal scores
        )
        .limit(limit)
        .offset(offset)
    )
    return {
        "findings": [_finding_dto(f) for f in result.scalars().all()],
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/risk-summary")
async def get_risk_summary(
    top: int = 5,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the tenant's risk overview (spec R5).

    ``severity_counts`` (full 5-key shape), average and maximum ``risk_score``,
    open-finding count, and the top ``top`` findings by risk. Empty tenants
    get zeroed metrics and an empty list — a 200, never an error.
    """
    top = max(1, min(top, 100))
    top_result = await db.execute(
        select(Finding)
        .where(Finding.tenant_id == user.tenant_id)
        .order_by(
            Finding.risk_score.desc().nullslast(),
            Finding.title.asc(),
        )
        .limit(top)
    )
    return {
        **await _risk_metrics(db, user.tenant_id),
        "top_findings": [_finding_dto(f) for f in top_result.scalars().all()],
    }


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return one of the tenant's assets with its findings (spec R6).

    The tenant filter turns both a cross-tenant id and a nonexistent id into
    the same 404 — no data leak, no existence oracle. Malformed ids 404 too.
    """
    parsed = _coerce_uuid(asset_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset_result = await db.execute(
        select(Asset).where(
            Asset.id == parsed,
            Asset.tenant_id == user.tenant_id,
        )
    )
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    findings_result = await db.execute(
        select(Finding)
        .where(
            Finding.asset_id == asset.id,
            Finding.tenant_id == user.tenant_id,
        )
        .order_by(
            Finding.risk_score.desc().nullslast(),
            Finding.title.asc(),
        )
    )
    return {
        "asset": _asset_dto(asset),
        "findings": [_finding_dto(f) for f in findings_result.scalars().all()],
    }


class FindingStatusUpdate(BaseModel):
    """Accepted status transitions — spec R7 domain ``open|resolved|fp``."""

    status: Literal["open", "resolved", "fp"]


@router.patch("/findings/{finding_id}")
async def update_finding_status(
    finding_id: str,
    body: FindingStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a finding's status and recompute the owning asset's aggregate.

    Spec R7: ``{"status": "resolved"|"fp"}`` over the domain
    ``open|resolved|fp``. An invalid value is rejected by Pydantic with 422
    before touching the row; a cross-tenant or unknown id returns 404 with no
    data leak. ``recompute_asset_risk`` keeps ``Asset.risk_score`` = max of
    open findings after every change (same path the scanner uses).
    """
    parsed = _coerce_uuid(finding_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    result = await db.execute(
        select(Finding).where(
            Finding.id == parsed,
            Finding.tenant_id == user.tenant_id,
        )
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = body.status
    await recompute_asset_risk(db, finding.asset_id)
    await db.commit()
    await db.refresh(finding)
    return _finding_dto(finding)


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
