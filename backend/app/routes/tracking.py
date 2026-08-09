"""Public tracking routes (Phase 4, PR 4) — token-gated, NO authentication.

External recipients interact through the links distributed at campaign launch
(design D1): the open pixel, the click redirect, the landing page, the
simulated credential form and the report action. Every access records an
``Event`` (design D3) carrying the request IP + user-agent (spec R5).
Unknown tokens → 404 and expired campaigns → 410, and in BOTH cases no Event
is recorded (spec R1/R2/R3/R5).

Security decisions:
- D5: ``/track/click`` ALWAYS 302-redirects to ``/l/{token}``. The ``?url=``
  query param is recorded in click metadata only and never followed, so the
  public endpoint cannot be abused as an open redirector.
- D4: credential submissions are hashed one-way (SHA-256) and the plaintext
  is discarded before any persistence — only hashes reach Event.metadata.
"""

import struct
import zlib
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.campaign import Campaign
from app.models.target import Target
from app.models.template import Template
from app.services.phishing.events import record_event
from app.services.phishing.landing import (
    credential_hash,
    resolve_tracking_target,
    sha256_hex,
)
from app.services.phishing.render import render

router = APIRouter(tags=["tracking"])  # public — no prefix, no auth dependency


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


# 1×1 transparent RGBA pixel, built once at import (spec R1).
_TRANSPARENT_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
    + _png_chunk(b"IEND", b"")
)


def _request_metadata(request: Request, **extra) -> dict:
    """Request context recorded on every Event (spec R5: ip + user-agent)."""
    meta = {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    meta.update(extra)
    return meta


def _click_tracking_url(token: str) -> str:
    """The ``{{link}}`` value: click tracking URL carrying the landing page as bait.

    D5: ``?url=`` is metadata-only at the click endpoint; the bait is the
    landing page itself (the model has no per-campaign bait field).
    """
    landing = f"{settings.tracking_base_url}/l/{token}"
    return f"{settings.tracking_base_url}/track/click/{token}?url={quote(landing, safe='')}"


def _landing_page_html(rendered_body: str, token: str) -> str:
    """Wrap the rendered template with the simulated-capture notice + form (R3)."""
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>Verificación de seguridad</title></head><body>"
        + rendered_body
        + '<p><strong>Simulación de phishing:</strong> este formulario forma parte '
        + "de una campaña de concientización autorizada. Las credenciales no se "
        + "almacenan.</p>"
        + f'<form method="post" action="/l/{token}/submit">'
        + '<p><label>Usuario <input type="text" name="username" required></label></p>'
        + '<p><label>Contraseña <input type="password" name="password" required></label></p>'
        + '<p><button type="submit">Ingresar</button></p>'
        + "</form>"
        + f'<p><a href="/l/{token}/report">Reportar este correo como phishing</a></p>'
        + "</body></html>"
    )


def _success_page_html() -> str:
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>Simulación completada</title></head><body>"
        "<h1>Simulación completada</h1>"
        "<p>Estas credenciales formaban parte de una simulación de phishing "
        "autorizada. Solo se registró su hash — el texto original fue descartado.</p>"
        "</body></html>"
    )


def _report_confirmation_html() -> str:
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>Gracias</title></head><body>"
        "<h1>Gracias</h1>"
        "<p>Este correo fue reportado. El equipo de seguridad registró tu reporte.</p>"
        "</body></html>"
    )


async def _resolve_or_404(
    db: AsyncSession, token: str
) -> tuple[Target, Campaign]:
    """Return ``(Target, Campaign)`` for a valid token; 404 unknown, 410 expired.

    Matches ``resolve_tracking_target``'s contract: ``None`` = unknown token
    (404) and ``expired=True`` = closed tracking window (410). No Event is
    recorded in either case (spec R1/R2/R5).
    """
    resolved = await resolve_tracking_target(db, token)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Tracking link not found")
    target, campaign, expired = resolved
    if expired:
        raise HTTPException(status_code=410, detail="Tracking link expired")
    return target, campaign


@router.get("/track/open/{token}.png")
async def track_open(
    token: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """1×1 transparent pixel + ``open`` Event (spec R1).

    ``Cache-Control: no-store`` ensures every open is counted. Unknown token
    → 404, expired campaign → 410, and no Event either way.
    """
    target, _ = await _resolve_or_404(db, token)
    await record_event(
        db,
        tenant_id=target.tenant_id,
        campaign_id=target.campaign_id,
        target_id=target.id,
        type="open",
        metadata=_request_metadata(request),
    )
    return Response(
        content=_TRANSPARENT_PIXEL_PNG,
        media_type="image/png",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@router.get("/track/click/{token}")
async def track_click(
    token: str,
    request: Request,
    url: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Record ``click`` and 302 → the landing page (spec R2 + design D5).

    The ``?url=`` bait is stored in Event metadata only and is NEVER used as
    the redirect target — the public endpoint cannot be an open redirector.
    """
    target, _ = await _resolve_or_404(db, token)
    await record_event(
        db,
        tenant_id=target.tenant_id,
        campaign_id=target.campaign_id,
        target_id=target.id,
        type="click",
        metadata=_request_metadata(request, url=url),
    )
    return Response(
        status_code=302,
        headers={"Location": f"/l/{token}", "Cache-Control": "no-store"},
    )


@router.get("/l/{token}")
async def landing_page(
    token: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Render the campaign template with per-target variables (spec R3).

    Substitutes ``{{nombre}}``/``{{link}}`` (design D7; missing keys render
    empty), appends the simulated-capture notice + credential form, and
    records a ``landing`` Event (design D3). 404 unknown, 410 expired.
    """
    target, campaign = await _resolve_or_404(db, token)
    template = await db.get(Template, campaign.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    body = render(
        template.html_body,
        {"nombre": target.name, "link": _click_tracking_url(token)},
    )
    await record_event(
        db,
        tenant_id=target.tenant_id,
        campaign_id=target.campaign_id,
        target_id=target.id,
        type="landing",
        metadata=_request_metadata(request),
    )
    return HTMLResponse(
        content=_landing_page_html(body, token),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/l/{token}/submit")
async def submit_credentials(
    token: str,
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Simulated credential capture (spec R4 + design D4).

    Hashes username/password one-way (SHA-256) and discards the plaintext —
    only hashes reach Event.metadata (``username_sha256``,
    ``password_sha256`` and the D4 combined ``hash``). Returns a success page
    (200). 404 unknown, 410 expired.
    """
    target, _ = await _resolve_or_404(db, token)
    await record_event(
        db,
        tenant_id=target.tenant_id,
        campaign_id=target.campaign_id,
        target_id=target.id,
        type="credential",
        metadata=_request_metadata(
            request,
            username_sha256=sha256_hex(username),
            password_sha256=sha256_hex(password),
            hash=credential_hash(username, password),
        ),
    )
    return HTMLResponse(content=_success_page_html())


@router.post("/l/{token}/report")
async def report_link(
    token: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Record a ``report`` Event — a recipient flagged the email (spec R6)."""
    target, _ = await _resolve_or_404(db, token)
    await record_event(
        db,
        tenant_id=target.tenant_id,
        campaign_id=target.campaign_id,
        target_id=target.id,
        type="report",
        metadata=_request_metadata(request),
    )
    return HTMLResponse(content=_report_confirmation_html())
