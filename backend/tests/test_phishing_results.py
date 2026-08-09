"""Phishing results + export tests (Phase 5, PR 5).

Covers the phishing-results spec R1-R3 as resolved for PR 5: per-target
results (``GET /phishing/campaigns/{id}/results``), the tenant aggregate
(``GET /phishing/results-summary``) and CSV/PDF export
(``GET /phishing/campaigns/{id}/export?format=csv|pdf`` — the PR-5 resolved
replacement for spec R3's ``/report`` endpoint).

Split across the two work-unit commits of PR 5, following the PR 4 pattern:
the unit layer (this file, commit 1) covers the pure service/generator
functions with no routes; the integration layer (commit 2) exercises the
auth'd endpoints over the SQLite ASGITransport client.

Selective run: ``pytest tests/test_phishing_results.py -q``
"""

import csv
import io
from datetime import datetime, timezone
from types import SimpleNamespace

from tests.test_asm import _register_and_login
from tests.test_export import _pdf_text_tokens
from tests.test_phishing_tracking import _launched_campaign

from app.services.phishing.results import (
    TargetResult,
    build_target_result,
    generate_results_csv,
    summarize,
)
from app.services.reports.phishing_pdf import ExportCampaignTarget, generate_campaign_pdf

CSV_HEADERS = ["email", "name", "status", "opened", "clicked", "credential", "reported"]


async def _record_activity(
    client,
    token: str,
    *,
    open: bool = True,
    click: bool = False,
    credential: bool = False,
    report: bool = False,
) -> None:
    """Simulate a target's tracking activity via the public endpoints."""
    if open:
        await client.get(f"/track/open/{token}.png")
    if click:
        await client.get(f"/track/click/{token}")
    if credential:
        await client.post(f"/l/{token}/submit", data={"username": "u", "password": "p"})
    if report:
        await client.post(f"/l/{token}/report")


def _campaign_like(**overrides) -> SimpleNamespace:
    fields = {"name": "Campaña de prueba", "status": "active"}
    fields.update(overrides)
    return SimpleNamespace(**fields)


# ── Unit: build_target_result (spec R1 per-target shape) ─────────────────────


class TestBuildTargetResult:
    def test_no_events_all_flags_false_timestamps_none(self):
        result = build_target_result(
            email="ana@x.com", name="Ana García", status="active", event_times={}
        )
        assert result.email == "ana@x.com"
        assert result.name == "Ana García"
        assert result.status == "active"
        assert result.opened is False
        assert result.clicked is False
        assert result.credential is False
        assert result.reported is False
        assert result.opened_at is None
        assert result.clicked_at is None
        assert result.credential_at is None
        assert result.reported_at is None

    def test_mixed_activity_flags_and_first_event_timestamps(self):
        opened_at = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        clicked_at = datetime(2026, 8, 1, 10, 5, tzinfo=timezone.utc)
        cred_at = datetime(2026, 8, 1, 10, 7, tzinfo=timezone.utc)
        result = build_target_result(
            email="bob@x.com",
            name="Bob",
            status="active",
            event_times={"open": opened_at, "click": clicked_at, "credential": cred_at},
        )
        assert result.opened is True and result.opened_at == opened_at
        assert result.clicked is True and result.clicked_at == clicked_at
        assert result.credential is True and result.credential_at == cred_at
        assert result.reported is False and result.reported_at is None

    def test_landing_and_unknown_types_do_not_flip_result_flags(self):
        """D3 audits ``landing`` but only open/click/credential/report surface."""
        result = build_target_result(
            email="c@x.com",
            name="C",
            status="active",
            event_times={"landing": datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc)},
        )
        assert result.opened is False
        assert result.clicked is False
        assert result.credential is False
        assert result.reported is False


# ── Unit: summarize (spec R2 aggregate counts + rates) ───────────────────────


class TestSummarize:
    def test_counts_and_rates_from_real_data(self):
        results = [
            TargetResult(
                email="a@x.com", name="A", status="active",
                opened=True, clicked=True, credential=True, reported=False,
            ),
            TargetResult(
                email="b@x.com", name="B", status="active",
                opened=True, clicked=False, credential=False, reported=True,
            ),
            TargetResult(
                email="c@x.com", name="C", status="active",
                opened=False, clicked=False, credential=False, reported=False,
            ),
            TargetResult(
                email="d@x.com", name="D", status="pending",
                opened=False, clicked=False, credential=False, reported=False,
            ),
        ]
        summary = summarize(results)
        assert summary.total_targets == 4
        assert summary.sent == 3  # only active targets were delivered
        assert summary.opened_count == 2
        assert summary.opened_rate == round(2 / 3 * 100, 2)  # 66.67%
        assert summary.clicked_count == 1
        assert summary.clicked_rate == round(1 / 3 * 100, 2)  # 33.33%
        assert summary.credentials_count == 1
        assert summary.reported_count == 1

    def test_empty_returns_zero_counts_and_zero_rates(self):
        """Spec R2 empty-tenant scenario: 200-shaped zeros, never an error."""
        summary = summarize([])
        assert summary.total_targets == 0
        assert summary.sent == 0
        assert summary.opened_count == 0
        assert summary.opened_rate == 0.0
        assert summary.clicked_count == 0
        assert summary.clicked_rate == 0.0
        assert summary.credentials_count == 0
        assert summary.reported_count == 0


# ── Unit: generate_results_csv (PR-5 CSV export) ─────────────────────────────


class TestGenerateResultsCsv:
    def test_headers_and_one_row_per_target(self):
        rows = [
            TargetResult(
                email="ana@x.com", name="Ana García", status="active",
                opened=True, clicked=True, credential=False, reported=False,
            ),
            TargetResult(
                email="bob@x.com", name="Bob", status="active",
                opened=False, clicked=False, credential=False, reported=True,
            ),
        ]
        parsed = list(csv.reader(io.StringIO(generate_results_csv(rows))))
        assert parsed[0] == CSV_HEADERS
        assert parsed[1] == ["ana@x.com", "Ana García", "active", "true", "true", "false", "false"]
        assert parsed[2] == ["bob@x.com", "Bob", "active", "false", "false", "false", "true"]

    def test_empty_returns_headers_only(self):
        parsed = list(csv.reader(io.StringIO(generate_results_csv([]))))
        assert parsed == [CSV_HEADERS]


# ── Unit: generate_campaign_pdf (spec R3 / PR-5 PDF export) ──────────────────


class TestGenerateCampaignPdf:
    def test_pdf_with_data_has_title_summary_and_table(self):
        campaign = _campaign_like(name="Alerta de seguridad")
        targets = [
            ExportCampaignTarget(
                email="ana@x.com", name="Ana", status="active",
                opened=True, clicked=True, credential=True, reported=False,
            ),
            ExportCampaignTarget(
                email="bob@x.com", name="Bob", status="active",
                opened=True, clicked=False, credential=False, reported=True,
            ),
            ExportCampaignTarget(
                email="carl@x.com", name="Carl", status="active",
                opened=False, clicked=False, credential=False, reported=False,
            ),
        ]
        pdf = generate_campaign_pdf(campaign, targets)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 1000
        text = _pdf_text_tokens(pdf)
        assert "Alerta de seguridad" in text
        assert "Results Summary" in text
        assert "ana@x.com" in text  # per-target table rows are rendered
        assert "bob@x.com" in text
        assert "carl@x.com" in text
        assert "Yes" in text  # opened/clicked/credential cells
        assert "66.67%" in text  # opened rate = 2 of 3 active targets

    def test_pdf_empty_campaign_zeroed(self):
        """Spec R3 empty-campaign scenario: valid PDF, zeroed metrics + note."""
        pdf = generate_campaign_pdf(_campaign_like(), [])
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 500
        text = _pdf_text_tokens(pdf)
        assert "No targets" in text
        assert "0%" in text  # rates fall back to 0%


# ── Integration: GET /phishing/campaigns/{id}/results (spec R1) ──────────────


class TestResultsEndpoint:
    async def test_results_require_auth(self, client):
        resp = await client.get(
            "/phishing/campaigns/00000000-0000-0000-0000-000000000000/results",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert resp.status_code == 401

    async def test_results_reflect_mixed_activity(self, client):
        headers = await _register_and_login(client, "res@test.com", "Res Corp")
        cid, tokens = await _launched_campaign(client, headers)
        await _record_activity(client, tokens["Ana García"], click=True, credential=True)
        await _record_activity(client, tokens["Bob Pérez"], open=False, report=True)

        resp = await client.get(f"/phishing/campaigns/{cid}/results", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["campaign_id"] == cid
        by_email = {t["email"]: t for t in body["targets"]}
        assert set(by_email) == {"ana@x.com", "bob@x.com"}

        ana = by_email["ana@x.com"]
        assert ana["name"] == "Ana García"
        assert ana["status"] == "active"
        assert ana["opened"] is True and ana["opened_at"] is not None
        assert ana["clicked"] is True and ana["clicked_at"] is not None
        assert ana["credential"] is True and ana["credential_at"] is not None
        assert ana["reported"] is False and ana["reported_at"] is None

        bob = by_email["bob@x.com"]
        assert bob["opened"] is False and bob["opened_at"] is None
        assert bob["clicked"] is False
        assert bob["credential"] is False
        assert bob["reported"] is True and bob["reported_at"] is not None

    async def test_results_no_activity_all_flags_false(self, client):
        headers = await _register_and_login(client, "resno@test.com", "Res No")
        cid, _ = await _launched_campaign(client, headers)

        resp = await client.get(f"/phishing/campaigns/{cid}/results", headers=headers)
        assert resp.status_code == 200
        for target in resp.json()["targets"]:
            assert target["opened"] is False
            assert target["clicked"] is False
            assert target["credential"] is False
            assert target["reported"] is False
            assert target["opened_at"] is None

    async def test_results_unknown_campaign_404(self, client):
        headers = await _register_and_login(client, "resunk@test.com", "Res Unk")
        resp = await client.get(
            "/phishing/campaigns/00000000-0000-0000-0000-000000000000/results",
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_results_cross_tenant_404(self, client):
        """R1 cross-tenant scenario: tenant B cannot read tenant A's results."""
        headers_a = await _register_and_login(client, "riso-a@test.com", "Riso A Corp")
        cid, tokens = await _launched_campaign(client, headers_a)
        await _record_activity(client, tokens["Ana García"], click=True)

        headers_b = await _register_and_login(client, "riso-b@test.com", "Riso B Corp")
        resp = await client.get(f"/phishing/campaigns/{cid}/results", headers=headers_b)
        assert resp.status_code == 404


# ── Integration: GET /phishing/results-summary (spec R2) ─────────────────────


class TestResultsSummary:
    async def test_summary_requires_auth(self, client):
        resp = await client.get(
            "/phishing/results-summary",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert resp.status_code == 401

    async def test_summary_aggregates_tenant_data(self, client):
        headers = await _register_and_login(client, "sum@test.com", "Sum Corp")
        _, tokens = await _launched_campaign(client, headers)  # 2 active targets
        await _record_activity(client, tokens["Ana García"], click=True, credential=True)
        await _record_activity(client, tokens["Bob Pérez"], open=False, report=True)

        resp = await client.get("/phishing/results-summary", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_targets"] == 2
        assert body["sent"] == 2
        assert body["opened_count"] == 1
        assert body["opened_rate"] == 50.0
        assert body["clicked_count"] == 1
        assert body["clicked_rate"] == 50.0
        assert body["credentials_count"] == 1
        assert body["reported_count"] == 1

    async def test_summary_empty_tenant_zeros(self, client):
        """R2 empty-tenant scenario: 200 with zero counts and 0% rates."""
        headers = await _register_and_login(client, "sumzero@test.com", "Sum Zero")
        resp = await client.get("/phishing/results-summary", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_targets"] == 0
        assert body["sent"] == 0
        assert body["opened_count"] == 0
        assert body["opened_rate"] == 0.0
        assert body["clicked_count"] == 0
        assert body["clicked_rate"] == 0.0
        assert body["credentials_count"] == 0
        assert body["reported_count"] == 0

    async def test_summary_is_tenant_scoped(self, client):
        """R2 from-real-data scenario: tenant B's summary never sees tenant A."""
        headers_a = await _register_and_login(client, "siso-a@test.com", "Siso A Corp")
        _, tokens = await _launched_campaign(client, headers_a)
        await _record_activity(client, tokens["Ana García"], click=True)

        headers_b = await _register_and_login(client, "siso-b@test.com", "Siso B Corp")
        resp = await client.get("/phishing/results-summary", headers=headers_b)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_targets"] == 0
        assert body["sent"] == 0
        assert body["opened_count"] == 0
        assert body["opened_rate"] == 0.0


# ── Integration: GET /phishing/campaigns/{id}/export (PR-5 spec R3) ──────────


class TestExportEndpoint:
    async def test_csv_export_columns_and_content_type(self, client):
        headers = await _register_and_login(client, "expcsv@test.com", "Exp Csv")
        cid, tokens = await _launched_campaign(client, headers)
        await _record_activity(client, tokens["Ana García"], click=True, credential=True)
        await _record_activity(client, tokens["Bob Pérez"], open=False, report=True)

        resp = await client.get(
            f"/phishing/campaigns/{cid}/export", params={"format": "csv"}, headers=headers
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "attachment" in resp.headers["content-disposition"]
        rows = list(csv.reader(io.StringIO(resp.text)))
        assert rows[0] == CSV_HEADERS
        assert len(rows) == 3  # header + 2 targets
        by_email = {r[0]: r for r in rows[1:]}
        assert by_email["ana@x.com"][3:] == ["true", "true", "true", "false"]
        assert by_email["bob@x.com"][3:] == ["false", "false", "false", "true"]

    async def test_pdf_export_valid_header(self, client):
        headers = await _register_and_login(client, "exppdf@test.com", "Exp Pdf")
        cid, tokens = await _launched_campaign(client, headers)
        await _record_activity(client, tokens["Ana García"], click=True)

        resp = await client.get(
            f"/phishing/campaigns/{cid}/export", params={"format": "pdf"}, headers=headers
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/pdf")
        assert "attachment" in resp.headers["content-disposition"]
        assert resp.content[:4] == b"%PDF"
        assert len(resp.content) > 1000

    async def test_pdf_export_empty_campaign(self, client):
        """Spec R3 empty-campaign scenario through the real endpoint."""
        headers = await _register_and_login(client, "exppdfe@test.com", "Exp Pdf E")
        tpl = await client.post(
            "/phishing/templates",
            json={
                "name": "Alerta",
                "subject": "Aviso {{nombre}}",
                "html_body": "<p>{{nombre}}</p>",
                "category": "bank",
            },
            headers=headers,
        )
        camp = await client.post(
            "/phishing/campaigns",
            json={"name": "Vacía", "template_id": tpl.json()["id"]},
            headers=headers,
        )
        cid = camp.json()["id"]

        resp = await client.get(
            f"/phishing/campaigns/{cid}/export", params={"format": "pdf"}, headers=headers
        )
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"
        text = _pdf_text_tokens(resp.content)
        assert "No targets" in text

    async def test_export_invalid_format_400(self, client):
        headers = await _register_and_login(client, "expbad@test.com", "Exp Bad")
        cid, _ = await _launched_campaign(client, headers)
        resp = await client.get(
            f"/phishing/campaigns/{cid}/export", params={"format": "docx"}, headers=headers
        )
        assert resp.status_code == 400

    async def test_export_missing_format_400(self, client):
        headers = await _register_and_login(client, "expnone@test.com", "Exp None")
        cid, _ = await _launched_campaign(client, headers)
        resp = await client.get(f"/phishing/campaigns/{cid}/export", headers=headers)
        assert resp.status_code == 400

    async def test_export_cross_tenant_404(self, client):
        headers_a = await _register_and_login(client, "exiso-a@test.com", "Exiso A Corp")
        cid, _ = await _launched_campaign(client, headers_a)

        headers_b = await _register_and_login(client, "exiso-b@test.com", "Exiso B Corp")
        resp = await client.get(
            f"/phishing/campaigns/{cid}/export", params={"format": "csv"}, headers=headers_b
        )
        assert resp.status_code == 404

    async def test_export_requires_auth(self, client):
        resp = await client.get(
            "/phishing/campaigns/00000000-0000-0000-0000-000000000000/export",
            params={"format": "csv"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert resp.status_code == 401
