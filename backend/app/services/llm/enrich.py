"""Optional-key LLM enrichment of findings (Groq via OpenAI-compatible SDK).

Design D4 / ADR-005: the ``openai`` SDK is pointed at Groq's base URL. The
API key is OPTIONAL — without it (or when a call fails) enrichment falls back
to deterministic per-finding_type templates, so the scan pipeline never
depends on an external LLM (spec R1).

Non-determinism + cost guard: findings that already have ``enriched_at`` set
are skipped in both the batch and on-demand paths (spec R4); the DB acts as
the cache (no Redis in infra today).
"""

import datetime
import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.asset import Asset
from app.models.finding import Finding

logger = logging.getLogger(__name__)

# Prompt the model sees. It MUST contain "JSON" for ``json_object`` mode
# (OpenAI-compatible requirement) and explicitly request the two fields the
# service persists (design: JSON ``{remediation, context}``).
_SYSTEM_PROMPT = (
    "You are a security analyst. Given a vulnerability finding, respond ONLY "
    'with a JSON object containing exactly two keys: "remediation" (concrete '
    'actionable remediation steps) and "context" (why the finding matters for '
    "this asset). Both values must be non-empty strings."
)

# Deterministic per-finding_type context templates (fallback path). These are
# static so a scan without an LLM key still produces useful, stable output.
_CONTEXT_TEMPLATES: dict[str, str] = {
    "missing-hsts": (
        "Without Strict-Transport-Security the site is exposed to "
        "protocol-downgrade and cookie-hijacking attacks over plain HTTP."
    ),
    "missing-xcto": (
        "Without X-Content-Type-Options the browser may MIME-sniff responses, "
        "enabling drive-by download of attacker-controlled content."
    ),
    "missing-csp": (
        "Without a Content-Security-Policy, a single XSS can load arbitrary "
        "remote scripts and exfiltrate tenant data."
    ),
    "insecure-cookie": (
        "Cookies without Secure/HttpOnly can be read by scripts or sent over "
        "plain HTTP, exposing sessions to theft."
    ),
    "tls-expired": (
        "An expired certificate breaks HTTPS trust; clients will refuse or "
        "bypass encryption, and the domain is effectively unprotected."
    ),
    "tls-self-signed": (
        "A self-signed certificate cannot be verified by clients, so traffic "
        "is vulnerable to on-path interception (MITM)."
    ),
    "tls-cn-mismatch": (
        "The certificate does not cover this hostname; browsers will reject "
        "the connection and users will see a security warning."
    ),
    "nonstandard-port": (
        "A service on a non-standard port is often unhardened and invisible "
        "to standard monitoring, increasing the exposed attack surface."
    ),
    "server-version-disclosure": (
        "A versioned Server header lets attackers match the software against "
        "known CVEs before probing it."
    ),
}

_DEFAULT_CONTEXT = (
    "This finding indicates a configuration weakness on the asset that "
    "should be reviewed and remediated."
)

# Used when a finding has no rule-provided remediation (legacy rows).
_DEFAULT_REMEDIATION = "Review the finding and apply the relevant hardening configuration."


@dataclass(frozen=True)
class EnrichmentResult:
    """The output persisted on a ``Finding`` by the enrichment path."""

    remediation: str
    context: str
    llm_summary: str | None  # raw LLM content; None when the template path ran
    enriched_at: datetime.datetime


def _build_client() -> AsyncOpenAI | None:
    """Lazily construct the OpenAI-compatible client when a key is set.

    Returns ``None`` when no ``LLM_API_KEY`` is configured (spec R1: key
    absent -> enrichment is inert and templates are used). Never raises.
    """
    if not settings.llm_enabled:
        return None
    return AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout,
    )


async def enrich_finding(
    finding: Finding,
    asset_context: dict | None = None,
) -> EnrichmentResult:
    """Enrich a single finding; ALWAYS returns a result (LLM or template).

    Never raises: a missing key, a failing client, an invalid shape or a
    network error all degrade to the deterministic template (spec R1).
    ``asset_context`` carries hostname/domain/port for the prompt; the caller
    supplies it (batch and on-demand paths resolve it from the Asset).
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    try:
        client = _build_client()
    except Exception as exc:  # noqa: BLE001 - a broken client config never fails a finding
        logger.warning("LLM client build failed, using template: %s", exc)
        client = None

    if client is None:
        return _template_result(finding, now)

    try:
        payload = await _call_llm(client, finding, asset_context or {})
    except Exception as exc:  # noqa: BLE001 - LLM failure must never fail the finding
        logger.warning("LLM enrichment failed for %s (%s): %s", finding.id, finding.finding_type, exc)
        payload = None

    if payload is None:
        return _template_result(finding, now)

    return EnrichmentResult(
        remediation=payload["remediation"],
        context=payload["context"],
        llm_summary=payload["raw"],
        enriched_at=now,
    )


async def _call_llm(
    client: AsyncOpenAI,
    finding: Finding,
    asset_context: dict,
) -> dict | None:
    """Call the model and return a shape-validated payload.

    Returns ``{remediation, context, raw}`` when the response is valid JSON
    with both fields non-empty; ``None`` when the shape is invalid (spec R4:
    malformed LLM output must not be persisted verbatim).
    """
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(finding, asset_context)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    payload = json.loads(content)
    remediation = (payload.get("remediation") or "").strip()
    context = (payload.get("context") or "").strip()
    if not remediation or not context:
        return None
    return {"remediation": remediation, "context": context, "raw": content}


def _build_prompt(finding: Finding, asset_context: dict) -> str:
    """One prompt per finding: title, detail, severity and asset context."""
    hostname = asset_context.get("hostname") or "unknown asset"
    return (
        f"Asset: {hostname}\n"
        f"Finding type: {finding.finding_type}\n"
        f"Severity: {finding.severity}\n"
        f"Title: {finding.title}\n"
        f"Detail: {finding.detail or ''}\n"
        f"Proposed remediation: {finding.remediation or ''}\n"
        'Respond with a JSON object: {"remediation": "...", "context": "..."}'
    )


def _template_result(finding: Finding, now: datetime.datetime) -> EnrichmentResult:
    """Deterministic per-finding_type template (design: fallback path)."""
    return EnrichmentResult(
        remediation=finding.remediation or _DEFAULT_REMEDIATION,
        context=_CONTEXT_TEMPLATES.get(finding.finding_type, _DEFAULT_CONTEXT),
        llm_summary=None,
        enriched_at=now,
    )


async def _asset_context(db: AsyncSession, asset_id, cache: dict | None = None) -> dict:
    """Resolve the Asset's hostname/domain/port for the prompt (cached per batch)."""
    if cache is not None and asset_id in cache:
        return cache[asset_id]
    asset = await db.get(Asset, asset_id)
    ctx = {}
    if asset is not None:
        ctx = {
            "hostname": asset.subdomain or asset.domain,
            "domain": asset.domain,
            "port": asset.port,
            "service": asset.service,
        }
    if cache is not None:
        cache[asset_id] = ctx
    return ctx


async def enrich_scan_findings(db: AsyncSession, scan_id) -> int:
    """Batch-enrich a scan's findings after scan completion (design R2).

    Skips findings that already have ``enriched_at`` (spec R4 — DB as cache),
    applies per-finding error handling (one failure never aborts the batch)
    and sets ``enriched_at`` even on the template path. Returns the number of
    findings enriched in this pass. Never raises; the caller owns the commit.
    """
    result = await db.execute(select(Finding).where(Finding.scan_id == scan_id))
    findings = result.scalars().all()

    asset_cache: dict = {}
    enriched = 0
    for finding in findings:
        if finding.enriched_at is not None:
            continue  # skip-already-enriched: cost + non-determinism guard
        try:
            ctx = await _asset_context(db, finding.asset_id, cache=asset_cache)
            out = await enrich_finding(finding, asset_context=ctx)
        except Exception as exc:  # noqa: BLE001 - one failure never aborts the batch
            logger.exception("Enrichment failed for finding %s: %s", finding.id, exc)
            continue

        finding.remediation = out.remediation
        finding.context = out.context
        finding.llm_summary = out.llm_summary
        finding.enriched_at = out.enriched_at
        enriched += 1

    await db.flush()
    return enriched
