"""Phishing templates API — tenant-scoped Template CRUD (Phase 2, PR 2).

Replaces the Phase 1 placeholder stub with real handlers backed by the
``Template`` model. Every endpoint is protected by ``get_current_user`` and
scoped to the authenticated user's ``tenant_id`` (app-level isolation, same
as ``asm.py`` — RLS is PostgreSQL-only, so this filter is what proves
isolation on SQLite). Seed templates (``tenant_id IS NULL``, design D9) are
readable by every tenant (list + detail) but are not editable/deletable —
PUT/DELETE scope strictly to the tenant's own rows, so a cross-tenant or
seed id yields 404 with no data leak (spec R2).

Phase 3 (PR 3) adds campaigns, targets upload and launch/cancel routes to
this router.
"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.template import Template
from app.models.user import User
from app.routes.auth import get_current_user

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
