"""Discovery orchestrator — wires the Phase 2 pure services into DB persistence.

This is the single entry point a scan route calls. It owns the ``Scan``
lifecycle (``running`` -> ``completed``/``error``) and persists discovered
``Asset`` rows (upserting on re-scan) plus ``Finding`` rows that the
fingerprint step reports.

Multi-tenant isolation is NOT enforced here: the caller passes the
authenticated ``tenant_id`` and every row is written with it. The app-level
filter lives in the routes (see ``routes/asm.py``) and is what proves
cross-tenant isolation on SQLite (RLS is PostgreSQL-only).

Each external call is bounded by a timeout drawn from ``config.settings`` so
a slow or unresponsive upstream source cannot stall a scan indefinitely.
"""

import datetime
import json
import logging

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.services import dns as dns_service
from app.services import enumerate as crtsh_service
from app.services import fingerprint as fp_service
from app.services import finding_rules as rules_service
from app.services.scoring import engine as scoring_engine

logger = logging.getLogger(__name__)

# Scan status values — mirror the Scan model lifecycle.
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"


async def run_scan(db: AsyncSession, tenant_id, domain: str) -> Scan:
    """Run passive + active discovery for a tenant and domain, persisting results.

    Workflow:
        1. Create a ``Scan(status=running, started_at)``.
        2. crt.sh subdomain enumeration (partial failure tolerated).
        3. For each subdomain: DNS A/AAAA resolve; skip unresolvable hosts.
        4. HTTP/TLS fingerprint the host.
        5. Upsert the ``Asset`` (preserve ``first_seen``, bump ``last_seen``).
        6. Persist any candidate findings.
        7. Mark the scan ``completed`` (or ``error`` on any uncaught failure).

    Args:
        db: The active async DB session.
        tenant_id: The authenticated tenant owning the scan.
        domain: The apex domain to scan.

    Returns:
        The persisted ``Scan``. On failure the scan carries ``status=error``
        and ``completed_at`` is set — the method never raises.
    """
    domain = domain.strip().lower()

    scan = Scan(tenant_id=tenant_id, domain=domain, status=STATUS_RUNNING)
    scan.started_at = datetime.datetime.now(datetime.timezone.utc)
    db.add(scan)
    await db.flush()  # obtain scan.id for finding rows

    try:
        # Passive enumeration. crt.sh failures are tolerated (partial result).
        subdomains = await crtsh_service.enumerate_subdomains(domain)

        for subdomain in subdomains:
            await _process_subdomain(db, scan, tenant_id, domain, subdomain)

        scan.status = STATUS_COMPLETED
        scan.completed_at = datetime.datetime.now(datetime.timezone.utc)
    except Exception as exc:  # noqa: BLE001 - a scan failure must not abort the request
        logger.exception("Attack-surface scan failed for %s: %s", domain, exc)
        scan.status = STATUS_ERROR
        scan.completed_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()
    await db.refresh(scan)
    return scan


async def _process_subdomain(
    db: AsyncSession,
    scan: Scan,
    tenant_id,
    domain: str,
    subdomain: str,
) -> None:
    """Resolve and fingerprint ``subdomain``, upserting its Asset + findings."""
    result = dns_service.resolve(subdomain, timeout=settings.dns_timeout)

    # Unresolvable host — skip (spec: no Asset row is created).
    if not result.ips:
        logger.info("Skipping unresolvable host %s", subdomain)
        return

    async with httpx.AsyncClient(timeout=settings.http_timeout, verify=False) as http:
        fr = await fp_service.fingerprint(
            subdomain,
            port=settings.fingerprint_port,
            scheme=settings.fingerprint_scheme,
            http=http,
        )

    asset = await _upsert_asset(
        db,
        tenant_id=tenant_id,
        domain=domain,
        subdomain=subdomain,
        ips=result.ips,
        fingerprint=fr.to_dict(),
    )

    await _persist_findings(db, scan, tenant_id, asset, fr)
    await recompute_asset_risk(db, asset.id)


async def _persist_findings(
    db: AsyncSession,
    scan: Scan,
    tenant_id,
    asset: Asset,
    fr,
) -> None:
    """Evaluate rules on the fingerprint, score candidates, persist Finding rows.

    Re-scan semantics (spec R3): the asset's previous findings are removed
    first, so the persisted set reflects the current scan — no history kept.
    """
    await db.execute(delete(Finding).where(Finding.asset_id == asset.id))

    fingerprint = fr.to_dict()
    for cand in rules_service.evaluate(fingerprint):
        scored = scoring_engine.score(cand.severity, cand.finding_type, fingerprint)
        db.add(
            Finding(
                tenant_id=tenant_id,
                asset_id=asset.id,
                scan_id=scan.id,
                severity=cand.severity,
                title=cand.title,
                detail=cand.detail,
                finding_type=cand.finding_type,
                risk_score=scored.risk_score,
                risk_level=scored.risk_level,
                remediation=cand.remediation,
                status="open",
            )
        )


async def recompute_asset_risk(db: AsyncSession, asset_id) -> float:
    """Recompute ``Asset.risk_score`` = max of the asset's open findings.

    Assets with no open findings score 0.0 (spec R3, NULL -> 0.0). Shared by
    the scan path and the finding-status PATCH path so both stay consistent.
    The caller owns the commit.
    """
    asset = await db.get(Asset, asset_id)
    if asset is None:
        return 0.0
    result = await db.execute(
        select(Finding.risk_score).where(
            Finding.asset_id == asset_id,
            Finding.status == "open",
        )
    )
    asset.risk_score = scoring_engine.aggregate_risk(result.scalars().all())
    await db.flush()
    return asset.risk_score


async def _upsert_asset(
    db: AsyncSession,
    tenant_id,
    domain: str,
    subdomain: str,
    ips: list[str],
    fingerprint: dict,
) -> Asset:
    """Update the existing Asset for (tenant, domain, subdomain) or insert one.

    On an existing row we bump ``last_seen``/``fingerprint``/``ip`` while
    preserving ``first_seen`` — the re-scan upsert contract.
    """
    result = await db.execute(
        select(Asset).where(
            Asset.tenant_id == tenant_id,
            Asset.domain == domain,
            Asset.subdomain == subdomain,
        )
    )
    asset = result.scalar_one_or_none()

    now = datetime.datetime.now(datetime.timezone.utc)
    if asset is not None:
        asset.ip = ips[0] if ips else None
        asset.port = settings.fingerprint_port
        asset.service = settings.fingerprint_scheme
        asset.fingerprint = json.dumps(fingerprint)
        asset.status = "discovered"
        asset.last_seen = now
        return asset

    asset = Asset(
        tenant_id=tenant_id,
        domain=domain,
        subdomain=subdomain,
        ip=ips[0] if ips else None,
        port=settings.fingerprint_port,
        service=settings.fingerprint_scheme,
        fingerprint=json.dumps(fingerprint),
        status="discovered",
        first_seen=now,
        last_seen=now,
    )
    db.add(asset)
    await db.flush()  # obtain asset.id for finding rows
    return asset
