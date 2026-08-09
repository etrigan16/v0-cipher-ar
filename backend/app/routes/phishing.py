"""Phishing API — tenant-scoped Template + Campaign/Target routes.

Templates (Phase 2, PR 2): every endpoint is protected by
``get_current_user`` and scoped to the authenticated user's ``tenant_id``
(app-level isolation, same as ``asm.py`` — RLS is PostgreSQL-only, so this
filter is what proves isolation on SQLite). Seed templates (``tenant_id IS
NULL``, design D9) are readable by every tenant (list + detail) but are not
editable/deletable — PUT/DELETE scope strictly to the tenant's own rows, so
a cross-tenant or seed id yields 404 with no data leak (spec R2).

Campaigns/Targets (Phase 3, PR 3): campaign CRUD, CSV target upload (stdlib
``csv``, validated in memory, one bulk insert — 422 with zero persisted,
design D6), launch (unique ``token_urlsafe(16)`` tracking tokens per target,
draft-only, needs ≥1 target) and cancel (draft|active → cancelled). Every
campaign/target query filters on ``tenant_id``; cross-tenant or unknown ids
are the same 404 (spec R6, no existence oracle).
"""

import csv
import io
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, EmailStr, TypeAdapter, ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.campaign import Campaign
from app.models.event import Event
from app.models.target import Target
from app.models.template import Template
from app.models.user import User
from app.routes.auth import get_current_user
from app.services.phishing.results import (
    TargetResult,
    build_target_result,
    generate_results_csv,
    summarize,
)
from app.services.phishing.tokens import generate_tracking_token
from app.services.reports.phishing_pdf import ExportCampaignTarget, generate_campaign_pdf

router = APIRouter(prefix="/phishing", tags=["phishing"])

# Template categories — spec R1 / migration 005 seeds (bank|government|tech).
TemplateCategory = Literal["bank", "government", "tech"]


class TemplateCreate(BaseModel):
    name: str
    subject: str
    html_body: str
    category: TemplateCategory


class TemplateUpdate(BaseModel):
    name: str
    subject: str
    html_body: str
    category: TemplateCategory


class TemplateDTO(BaseModel):
    id: str
    name: str
    subject: str
    html_body: str
    category: str
    created_at: datetime


def _coerce_uuid(value: str) -> uuid.UUID | None:
    """Return the UUID when ``value`` parses, else ``None`` (invalid input).

    Mirrors ``asm.py``: filter values that are not valid UUIDs must not
    raise in the ``CoercingUuid`` bind processor; ``None`` means "no match".
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


def _template_dto(t: Template) -> TemplateDTO:
    return TemplateDTO(
        id=str(t.id),
        name=t.name,
        subject=t.subject,
        html_body=t.html_body,
        category=t.category,
        created_at=t.created_at,
    )


# ── Campaign / Target contracts (Phase 3, PR 3) ──────────────────────────────

# Campaign lifecycle — spec R1 domain ``draft|active|completed|cancelled``.
CampaignStatus = Literal["draft", "active", "completed", "cancelled"]


class CampaignCreate(BaseModel):
    name: str
    template_id: str


class CampaignUpdate(BaseModel):
    name: str
    template_id: str
    # Accepted for domain validation only (R1: out-of-domain status → 422).
    # Status transitions are owned by launch/cancel — never applied here.
    status: CampaignStatus | None = None


class CampaignDTO(BaseModel):
    id: str
    name: str
    template_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    target_count: int = 0


class TargetDTO(BaseModel):
    id: str
    email: str
    name: str
    status: str
    tracking_token: str | None
    created_at: datetime


def _campaign_dto(c: Campaign, target_count: int = 0) -> CampaignDTO:
    return CampaignDTO(
        id=str(c.id),
        name=c.name,
        template_id=str(c.template_id),
        status=c.status,
        started_at=c.started_at,
        completed_at=c.completed_at,
        created_at=c.created_at,
        target_count=target_count,
    )


def _target_dto(t: Target) -> TargetDTO:
    return TargetDTO(
        id=str(t.id),
        email=t.email,
        name=t.name,
        status=t.status,
        tracking_token=t.tracking_token,
        created_at=t.created_at,
    )


async def _get_owned_campaign(
    db: AsyncSession, campaign_id: str, tenant_id
) -> Campaign | None:
    """Return the tenant's campaign, else ``None`` (cross-tenant = 404, R6)."""
    parsed = _coerce_uuid(campaign_id)
    if parsed is None:
        return None
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == parsed,
            Campaign.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def _resolve_owned_template(
    db: AsyncSession, template_id: str, tenant_id
) -> uuid.UUID | None:
    """Resolve a template the tenant may use: own rows or shared seeds (D9).

    Returns the parsed UUID when the template exists and is owned by the
    tenant or is a NULL-tenant seed; ``None`` otherwise (404, no leak).
    """
    parsed = _coerce_uuid(template_id)
    if parsed is None:
        return None
    result = await db.execute(
        select(Template.id).where(
            Template.id == parsed,
            or_(
                Template.tenant_id == tenant_id,
                Template.tenant_id.is_(None),
            ),
        )
    )
    return parsed if result.scalar_one_or_none() is not None else None


async def _target_count(db: AsyncSession, campaign_id, tenant_id) -> int:
    return (
        await db.scalar(
            select(func.count())
            .select_from(Target)
            .where(
                Target.campaign_id == campaign_id,
                Target.tenant_id == tenant_id,
            )
        )
        or 0
    )


def _parse_targets_csv(text: str) -> list[tuple[str, str]]:
    """Parse ``(email,name)`` rows, validating everything in memory (D6).

    Raises ``ValueError`` on the first malformed row so the route returns
    422 with zero persisted targets (spec R2/R3). Emails are normalized via
    Pydantic ``EmailStr``; duplicates within the file are rejected. A header
    row (``email,name``) is tolerated and skipped.
    """
    reader = csv.reader(io.StringIO(text))
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for i, row in enumerate(reader):
        if i == 0 and row and row[0].strip().lower() == "email":
            continue  # header row
        if len(row) < 2 or not row[0].strip() or not row[1].strip():
            raise ValueError(f"Row {i + 1}: email and name are required")
        email = row[0].strip()
        try:
            email = str(TypeAdapter(EmailStr).validate_python(email))
        except ValidationError:
            raise ValueError(f"Row {i + 1}: invalid email {email!r}")
        if email.lower() in seen:
            raise ValueError(f"Row {i + 1}: duplicate email {email!r} in file")
        seen.add(email.lower())
        rows.append((email, row[1].strip()))
    if not rows:
        raise ValueError("CSV contains no target rows")
    return rows


@router.get("/templates")
async def list_templates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the tenant's templates plus the shared NULL-tenant seeds (R2/R3)."""
    result = await db.execute(
        select(Template)
        .where(
            or_(
                Template.tenant_id == user.tenant_id,
                Template.tenant_id.is_(None),  # seeds visible to every tenant (D9)
            )
        )
        .order_by(Template.created_at.desc())
    )
    return {"templates": [_template_dto(t) for t in result.scalars().all()]}


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a template owned by the current tenant (R1/R2)."""
    template = Template(
        tenant_id=user.tenant_id,
        name=body.name,
        subject=body.subject,
        html_body=body.html_body,
        category=body.category,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return _template_dto(template)


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return one template — own rows or shared seeds; else 404 (R2).

    The tenant filter turns a cross-tenant id, a seed id, and a nonexistent
    id into the same 404 — no data leak, no existence oracle. Malformed ids
    404 too (mirrors ``asm.py`` asset detail).
    """
    parsed = _coerce_uuid(template_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Template not found")

    result = await db.execute(
        select(Template).where(
            Template.id == parsed,
            or_(
                Template.tenant_id == user.tenant_id,
                Template.tenant_id.is_(None),
            ),
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_dto(template)


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    body: TemplateUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update one of the tenant's OWN templates (R2).

    Scoped strictly to ``tenant_id == user.tenant_id``: cross-tenant and
    shared seed templates are 404 — seeds are global and must not be
    modified by any single tenant.
    """
    parsed = _coerce_uuid(template_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Template not found")

    result = await db.execute(
        select(Template).where(
            Template.id == parsed,
            Template.tenant_id == user.tenant_id,
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    template.name = body.name
    template.subject = body.subject
    template.html_body = body.html_body
    template.category = body.category
    await db.commit()
    await db.refresh(template)
    return _template_dto(template)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete one of the tenant's OWN templates (R2).

    Same strict scoping as PUT: cross-tenant and seed ids are 404. The
    response is 204 with no body.
    """
    parsed = _coerce_uuid(template_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Template not found")

    result = await db.execute(
        select(Template).where(
            Template.id == parsed,
            Template.tenant_id == user.tenant_id,
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Campaign CRUD (Phase 3, PR 3) ────────────────────────────────────────────


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft campaign from a template the tenant may use (R1).

    The template must be tenant-owned or a shared seed (D9) — otherwise 404
    with no existence oracle. New campaigns always start as ``draft``.
    """
    template_uuid = await _resolve_owned_template(db, body.template_id, user.tenant_id)
    if template_uuid is None:
        raise HTTPException(status_code=404, detail="Template not found")

    campaign = Campaign(
        tenant_id=user.tenant_id,
        name=body.name,
        template_id=template_uuid,
        status="draft",
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return _campaign_dto(campaign)


@router.get("/campaigns")
async def list_campaigns(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the tenant's campaigns with per-campaign target counts (R2)."""
    count_subq = (
        select(func.count(Target.id))
        .where(
            Target.campaign_id == Campaign.id,
            Target.tenant_id == user.tenant_id,
        )
        .scalar_subquery()
    )
    result = await db.execute(
        select(Campaign, count_subq.label("target_count"))
        .where(Campaign.tenant_id == user.tenant_id)
        .order_by(Campaign.created_at.desc())
    )
    return {
        "campaigns": [
            _campaign_dto(campaign, target_count=count or 0)
            for campaign, count in result.all()
        ]
    }


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return one of the tenant's campaigns with its target count (R2/R6)."""
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _campaign_dto(
        campaign,
        target_count=await _target_count(db, campaign.id, user.tenant_id),
    )


@router.put("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    body: CampaignUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update name/template of a DRAFT campaign; else 409 (R2/R6).

    Cross-tenant or unknown ids are 404. ``body.status`` is validated for
    domain membership only (R1 — an out-of-domain value is 422); status
    transitions are owned by launch/cancel, never mutated here.
    """
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "draft":
        raise HTTPException(
            status_code=409, detail="Only draft campaigns can be updated"
        )

    template_uuid = await _resolve_owned_template(db, body.template_id, user.tenant_id)
    if template_uuid is None:
        raise HTTPException(status_code=404, detail="Template not found")

    campaign.name = body.name
    campaign.template_id = template_uuid
    await db.commit()
    await db.refresh(campaign)
    return _campaign_dto(campaign)


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a DRAFT campaign; non-draft → 409, cross-tenant/unknown → 404."""
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "draft":
        raise HTTPException(
            status_code=409, detail="Only draft campaigns can be deleted"
        )

    await db.delete(campaign)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Target CSV upload + listing (Phase 3, PR 3) ──────────────────────────────


@router.post(
    "/campaigns/{campaign_id}/targets/upload", status_code=status.HTTP_201_CREATED
)
async def upload_campaign_targets(
    campaign_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload targets from a ``(email,name)`` CSV into a draft campaign.

    Parsed and validated entirely in memory (design D6): any malformed row,
    duplicate within the file, or duplicate against existing campaign targets
    yields 422 with zero persisted rows (spec R2/R3). Valid rows are inserted
    in one bulk insert as ``pending`` with no tracking token (assigned at
    launch). Only draft campaigns accept uploads (409 otherwise).
    """
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "draft":
        raise HTTPException(
            status_code=409, detail="Only draft campaigns accept target uploads"
        )

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="CSV must be UTF-8 encoded")
    try:
        rows = _parse_targets_csv(text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    existing = await db.execute(
        select(Target.email).where(
            Target.campaign_id == campaign.id,
            Target.tenant_id == user.tenant_id,
        )
    )
    known = {email.lower() for (email,) in existing.all()}
    for email, _ in rows:
        if email.lower() in known:
            raise HTTPException(
                status_code=422,
                detail=f"Duplicate email {email!r} already exists in campaign",
            )

    targets = [
        Target(
            tenant_id=user.tenant_id,
            campaign_id=campaign.id,
            email=email,
            name=name,
            status="pending",
        )
        for email, name in rows
    ]
    db.add_all(targets)
    await db.commit()
    return {"count": len(targets), "targets": [_target_dto(t) for t in targets]}


@router.get("/campaigns/{campaign_id}/targets")
async def list_campaign_targets(
    campaign_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the campaign's targets, tenant-scoped (R6; cross-tenant → 404)."""
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    result = await db.execute(
        select(Target)
        .where(
            Target.campaign_id == campaign.id,
            Target.tenant_id == user.tenant_id,
        )
        .order_by(Target.created_at.asc())
    )
    return {"targets": [_target_dto(t) for t in result.scalars().all()]}


# ── Launch / cancel (Phase 3, PR 3 — spec R4/R5) ─────────────────────────────


@router.post("/campaigns/{campaign_id}/launch")
async def launch_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Launch a draft campaign with ≥1 target (spec R4, links-only).

    Every target gets a unique ``secrets.token_urlsafe(16)`` tracking token
    (design D1), the campaign becomes ``active`` with ``started_at`` set, and
    the per-target distributable landing links are returned. No emails are
    sent — delivery is links-only per the consent model. 409 when the
    campaign is not draft or has no targets; 404 cross-tenant/unknown.
    """
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "draft":
        raise HTTPException(
            status_code=409, detail="Only draft campaigns can be launched"
        )

    result = await db.execute(
        select(Target).where(
            Target.campaign_id == campaign.id,
            Target.tenant_id == user.tenant_id,
        )
    )
    targets = result.scalars().all()
    if not targets:
        raise HTTPException(
            status_code=409, detail="Campaign has no targets to launch"
        )

    campaign.status = "active"
    campaign.started_at = datetime.now(timezone.utc)
    for target in targets:
        target.tracking_token = generate_tracking_token()
        target.status = "active"
    await db.commit()

    return {
        "campaign": _campaign_dto(campaign),
        "targets": [
            {
                "id": str(t.id),
                "email": t.email,
                "name": t.name,
                "status": t.status,
                "tracking_token": t.tracking_token,
                "landing_url": f"{settings.tracking_base_url}/l/{t.tracking_token}",
            }
            for t in targets
        ],
    }


@router.post("/campaigns/{campaign_id}/cancel")
async def cancel_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a draft or active campaign (spec R5).

    Sets ``cancelled`` + ``completed_at``; tracking links of a cancelled
    campaign stop resolving (Phase 4 enforces expiry). Completed campaigns
    cannot be cancelled (409); cross-tenant/unknown ids are 404.
    """
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status not in ("draft", "active"):
        raise HTTPException(
            status_code=409,
            detail="Only draft or active campaigns can be cancelled",
        )

    campaign.status = "cancelled"
    campaign.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(campaign)
    return _campaign_dto(campaign)


# ── Results + export (Phase 5, PR 5 — spec R1/R2/R3) ─────────────────────────


def _result_dto(result: TargetResult) -> dict:
    """One per-target row: flags + first-event timestamps (spec R1)."""
    return {
        "email": result.email,
        "name": result.name,
        "status": result.status,
        "opened": result.opened,
        "opened_at": result.opened_at,
        "clicked": result.clicked,
        "clicked_at": result.clicked_at,
        "credential": result.credential,
        "credential_at": result.credential_at,
        "reported": result.reported,
        "reported_at": result.reported_at,
    }


async def _load_results(
    db: AsyncSession, *, tenant_id, campaign_id=None
) -> list[TargetResult]:
    """Build per-target results for a campaign (or the whole tenant).

    Targets and Events are both filtered on ``tenant_id`` (app-level
    isolation — RLS is PostgreSQL-only, so this filter is what proves
    isolation on SQLite, same as every other phishing route). Event
    aggregation uses ``MIN(occurred_at)`` per ``(target, type)`` so each
    flag carries the target's FIRST occurrence (spec R1 timestamps).
    """
    target_filters = [Target.tenant_id == tenant_id]
    event_filters = [Event.tenant_id == tenant_id]
    if campaign_id is not None:
        target_filters.append(Target.campaign_id == campaign_id)
        event_filters.append(Event.campaign_id == campaign_id)

    targets_result = await db.execute(
        select(Target).where(*target_filters).order_by(Target.created_at.asc())
    )
    targets = targets_result.scalars().all()

    events_result = await db.execute(
        select(
            Event.target_id,
            Event.type,
            func.min(Event.occurred_at),
        )
        .where(*event_filters)
        .group_by(Event.target_id, Event.type)
    )
    times: dict[uuid.UUID, dict[str, datetime]] = {}
    for target_id, event_type, occurred_at in events_result.all():
        times.setdefault(target_id, {})[event_type] = occurred_at

    return [
        build_target_result(
            email=t.email,
            name=t.name,
            status=t.status,
            event_times=times.get(t.id, {}),
        )
        for t in targets
    ]


@router.get("/campaigns/{campaign_id}/results")
async def get_campaign_results(
    campaign_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Per-target results for one campaign (spec R1).

    Each row carries the target's email/name/status and per-type activity
    flags + first-event timestamps (opened/clicked/credential/reported).
    Cross-tenant and unknown ids are the same 404 (no existence oracle).
    """
    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    results = await _load_results(
        db, tenant_id=user.tenant_id, campaign_id=campaign.id
    )
    return {
        "campaign_id": str(campaign.id),
        "targets": [_result_dto(r) for r in results],
    }


@router.get("/results-summary")
async def get_results_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tenant-wide results aggregate (spec R2).

    Counts (total/sent/opened/clicked/credentials/reported) and rates
    (open %, click %) are computed from the tenant's targets and Events
    only. A tenant with no activity gets zero counts and 0% rates with 200 —
    never an error (spec R2 empty-tenant scenario).
    """
    results = await _load_results(db, tenant_id=user.tenant_id)
    return asdict(summarize(results))


@router.get("/campaigns/{campaign_id}/export")
async def export_campaign_results(
    campaign_id: str,
    format: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export one campaign's results as CSV or PDF (PR-5 spec R3).

    ``format`` must be ``csv`` or ``pdf`` — anything else, including a
    missing value, is a 400 (mirrors ``asm.py`` export). The campaign must
    belong to the tenant (cross-tenant/unknown → 404). CSV is rendered with
    the stdlib ``csv`` writer; PDF reuses the risk-scoring reportlab stack
    (design D8). Both are returned as an attachment download.
    """
    if format not in ("csv", "pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid export format; expected 'csv' or 'pdf'",
        )

    campaign = await _get_owned_campaign(db, campaign_id, user.tenant_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    results = await _load_results(
        db, tenant_id=user.tenant_id, campaign_id=campaign.id
    )

    if format == "csv":
        content = generate_results_csv(results).encode("utf-8")
        media_type = "text/csv"
        filename = f"phishing-results-{str(campaign.id)[:8]}.csv"
    else:
        export_targets = [
            ExportCampaignTarget(
                email=r.email,
                name=r.name,
                status=r.status,
                opened=r.opened,
                clicked=r.clicked,
                credential=r.credential,
                reported=r.reported,
            )
            for r in results
        ]
        content = generate_campaign_pdf(campaign, export_targets)
        media_type = "application/pdf"
        filename = f"phishing-results-{str(campaign.id)[:8]}.pdf"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
