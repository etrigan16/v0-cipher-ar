"""Phase 4 (PR 3): LLM enrichment tests.

Selective run: ``pytest tests/test_llm_enrich.py -q``

The enrichment service must be functional with NO API key (deterministic
templates) and degrade gracefully when the LLM fails (spec R1). Findings that
already have ``enriched_at`` are skipped in batch and on-demand paths (spec
R4 — DB acts as cache; no Redis in infra). All LLM behavior is tested with a
mocked client; assertions check shape and flow, not exact LLM content (spec
R4 scenario "Deterministic tests").
"""

import datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.tenant import Tenant
from app.services import orchestrator
from app.services.llm import enrich as enrich_service

from test_asm import _patch_discovery


# ---------------------------------------------------------------------------
# Fakes for the OpenAI-compatible client (Groq). The service only touches
# ``client.chat.completions.create(...)``; these fakes stand in for the SDK.
# ---------------------------------------------------------------------------


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    """Records calls; returns queued responses or raises the configured error."""

    def __init__(self, responses=None, error=None):
        self.calls = []
        self._responses = list(responses or [])
        self._error = error

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        if self._responses:
            return self._responses.pop(0)
        return _FakeResponse(
            '{"remediation": "LLM remediation", "context": "LLM context"}'
        )


class _FakeChat:
    def __init__(self, completions: _FakeCompletions):
        self.completions = completions


class _FakeClient:
    """Duck-typed AsyncOpenAI: only ``chat.completions.create`` is exercised."""

    def __init__(self, responses=None, error=None):
        self.chat = _FakeChat(_FakeCompletions(responses=responses, error=error))


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    t = Tenant(name="Acme Corp", slug="acme-corp")
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


def _make_finding(
    tenant=None,
    *,
    finding_type: str = "missing-hsts",
    severity: str = "medium",
    remediation: str = "Add HSTS header to every HTTPS response.",
    enriched_at=None,
    asset_id=None,
    scan_id=None,
) -> Finding:
    # Unit-test findings are never persisted: a fixed dummy tenant id is fine.
    tenant_id = tenant.id if tenant is not None else "10000000-0000-0000-0000-000000000001"
    return Finding(
        tenant_id=tenant_id,
        asset_id=asset_id,
        scan_id=scan_id,
        severity=severity,
        title="Missing Strict-Transport-Security header",
        detail="The HTTPS response does not send Strict-Transport-Security.",
        finding_type=finding_type,
        risk_score=5.5,
        risk_level="medium",
        remediation=remediation,
        status="open",
        enriched_at=enriched_at,
    )


# ---------------------------------------------------------------------------
# Template fallback (no API key) — spec R1 "Key absent"
# ---------------------------------------------------------------------------


class TestTemplateFallback:
    async def test_key_absent_uses_template_and_keeps_rule_remediation(self):
        """R1/KeyAbsent: no client -> deterministic template; DB remediation preserved."""
        finding = _make_finding(tenant=None)  # type: ignore[arg-type]  # not persisted

        result = await enrich_service.enrich_finding(finding)

        # Uses the remediation already attached by the rules (spec R1: template
        # generator uses remediation from the rule result / DB).
        assert result.remediation == "Add HSTS header to every HTTPS response."
        # Deterministic per-finding_type context template (non-empty, meaningful).
        assert result.context
        assert "Strict-Transport-Security" in result.context
        assert result.enriched_at is not None
        assert result.llm_summary is None

    async def test_template_context_is_deterministic_per_type(self):
        """R1/KeyAbsent: same finding_type -> identical template output."""
        f1 = _make_finding(tenant=None, remediation="r1")  # type: ignore[arg-type]
        f2 = _make_finding(tenant=None, remediation="r2")  # type: ignore[arg-type]

        r1 = await enrich_service.enrich_finding(f1)
        r2 = await enrich_service.enrich_finding(f2)

        # Deterministic: same type -> same context regardless of remediation text.
        assert r1.context == r2.context
        # Remediation still comes from each finding's own rule output.
        assert r1.remediation == "r1"
        assert r2.remediation == "r2"

    async def test_template_falls_back_for_unknown_type(self):
        """R1/KeyAbsent: unknown finding_type gets the generic template."""
        finding = _make_finding(tenant=None, finding_type="brand-new-rule")  # type: ignore[arg-type]

        result = await enrich_service.enrich_finding(finding)

        assert result.context  # generic context, non-empty
        assert result.enriched_at is not None


# ---------------------------------------------------------------------------
# LLM success (mocked client) — spec R1 "Key configured"
# ---------------------------------------------------------------------------


class TestLLMSuccess:
    async def test_llm_payload_parsed_and_shape_validated(self, monkeypatch):
        """R1/KeyConfigured: valid JSON {remediation, context} is used verbatim."""
        finding = _make_finding(tenant=None)  # type: ignore[arg-type]
        fake = _FakeClient(
            responses=[
                _FakeResponse('{"remediation": "Fix A", "context": "Why A"}')
            ]
        )
        monkeypatch.setattr(enrich_service, "_build_client", lambda: fake)

        result = await enrich_service.enrich_finding(
            finding, asset_context={"hostname": "www.example.com"}
        )

        assert result.remediation == "Fix A"
        assert result.context == "Why A"
        assert result.llm_summary == '{"remediation": "Fix A", "context": "Why A"}'
        assert result.enriched_at is not None
        # The prompt carried title/detail/severity/asset context to the model.
        assert fake.chat.completions.calls, "LLM client must be called"
        messages = fake.chat.completions.calls[0]["messages"]
        user_prompt = messages[1]["content"]
        assert "Missing Strict-Transport-Security header" in user_prompt
        assert "www.example.com" in user_prompt
        assert "medium" in user_prompt

    async def test_llm_failure_falls_back_to_template(self, monkeypatch):
        """R1/LLMFailure: an exception mid-call degrades to the template, no raise."""
        finding = _make_finding(tenant=None)  # type: ignore[arg-type]
        fake = _FakeClient(error=RuntimeError("groq is down"))
        monkeypatch.setattr(enrich_service, "_build_client", lambda: fake)

        result = await enrich_service.enrich_finding(finding)

        assert result.remediation == "Add HSTS header to every HTTPS response."
        assert result.context
        assert result.llm_summary is None
        assert result.enriched_at is not None

    async def test_bad_shape_falls_back_to_template(self, monkeypatch):
        """R4/Shape: missing/blank required fields are never persisted verbatim."""
        for bad_content in (
            '{"remediation": "", "context": "only context"}',
            '{"remediation": "only remediation"}',
            "not json at all",
            "{}",
        ):
            finding = _make_finding(tenant=None)  # type: ignore[arg-type]
            fake = _FakeClient(responses=[_FakeResponse(bad_content)])
            monkeypatch.setattr(enrich_service, "_build_client", lambda: fake)

            result = await enrich_service.enrich_finding(finding)

            assert result.remediation == "Add HSTS header to every HTTPS response."
            assert result.context  # template context, not malformed LLM data
            assert result.llm_summary is None

    async def test_key_absent_never_builds_client(self, monkeypatch):
        """R1: without a key the client builder returns None and no SDK call happens."""
        monkeypatch.setattr(enrich_service.settings, "llm_api_key", "")

        assert enrich_service._build_client() is None


# ---------------------------------------------------------------------------
# Batch enrichment + skip-already-enriched — spec R2 "Batch after scan", R4
# ---------------------------------------------------------------------------


class TestBatchEnrichment:
    async def _seed_findings(self, db_session, tenant):
        asset = Asset(
            tenant_id=tenant.id, domain="example.com", subdomain="www.example.com"
        )
        scan = Scan(tenant_id=tenant.id, domain="example.com", status="completed")
        db_session.add_all([asset, scan])
        await db_session.flush()
        findings = [
            _make_finding(tenant, finding_type="missing-hsts", asset_id=asset.id, scan_id=scan.id),
            _make_finding(tenant, finding_type="missing-csp", asset_id=asset.id, scan_id=scan.id),
        ]
        db_session.add_all(findings)
        await db_session.commit()
        return scan, findings

    async def test_batch_enriches_all_findings_with_templates(
        self, db_session, tenant
    ):
        """R2/Batch: every eligible finding gets context + enriched_at (no key -> templates)."""
        scan, findings = await self._seed_findings(db_session, tenant)
        assert all(f.enriched_at is None for f in findings)

        count = await enrich_service.enrich_scan_findings(db_session, scan.id)

        assert count == 2
        await db_session.refresh(findings[0])
        await db_session.refresh(findings[1])
        assert findings[0].enriched_at is not None
        assert findings[0].context
        assert findings[1].enriched_at is not None
        assert findings[1].context

    async def test_batch_uses_llm_when_available(self, db_session, tenant, monkeypatch):
        """R2/Batch: with a key, findings get the LLM payload; enrichment persists."""
        scan, findings = await self._seed_findings(db_session, tenant)
        fake = _FakeClient(responses=[_FakeResponse('{"remediation": "R", "context": "C"}')] * 2)
        monkeypatch.setattr(enrich_service, "_build_client", lambda: fake)

        count = await enrich_service.enrich_scan_findings(db_session, scan.id)

        assert count == 2
        await db_session.refresh(findings[0])
        assert findings[0].remediation == "R"
        assert findings[0].context == "C"
        assert findings[0].llm_summary == '{"remediation": "R", "context": "C"}'

    async def test_batch_skips_already_enriched(self, db_session, tenant, monkeypatch):
        """R4/AlreadyEnriched: enriched_at set -> not re-enriched; values unchanged."""
        scan, findings = await self._seed_findings(db_session, tenant)
        already = findings[0]
        already.enriched_at = datetime.datetime.now(datetime.timezone.utc)
        already.remediation = "original remediation"
        await db_session.commit()

        # If the batch tried to re-enrich, the client would be called — it is not.
        fake = _FakeClient()
        monkeypatch.setattr(enrich_service, "_build_client", lambda: fake)

        count = await enrich_service.enrich_scan_findings(db_session, scan.id)

        assert count == 1  # only the not-yet-enriched finding was processed
        await db_session.refresh(already)
        assert already.remediation == "original remediation"
        assert already.enriched_at is not None
        # The skipped finding never reached the LLM; only the other one did.
        assert len(fake.chat.completions.calls) == 1

    async def test_batch_failure_does_not_abort(self, db_session, tenant, monkeypatch):
        """R1/LLMFailure: a failing LLM still enriches other findings (templates)."""
        scan, findings = await self._seed_findings(db_session, tenant)

        async def _flaky_build():
            raise RuntimeError("client init exploded")

        monkeypatch.setattr(enrich_service, "_build_client", _flaky_build)

        # enrich_scan_findings catches per-finding errors and keeps going.
        count = await enrich_service.enrich_scan_findings(db_session, scan.id)

        assert count == 2  # both fell back to templates via the internal guard
        await db_session.refresh(findings[0])
        await db_session.refresh(findings[1])
        assert findings[0].enriched_at is not None
        assert findings[0].context
        assert findings[1].enriched_at is not None

    async def test_orchestrator_run_scan_enriches_findings(self, db_session, tenant, monkeypatch):
        """R2/BatchAfterScan: run_scan leaves findings enriched (no key -> templates)."""
        _patch_discovery(monkeypatch)

        scan = await orchestrator.run_scan(
            db_session, tenant_id=tenant.id, domain="example.com"
        )

        assert scan.status == "completed"
        result = await db_session.execute(
            select(Finding).where(Finding.scan_id == scan.id)
        )
        findings = result.scalars().all()
        assert findings, "scan must produce findings"
        for finding in findings:
            assert finding.enriched_at is not None
            assert finding.context
            assert finding.remediation
