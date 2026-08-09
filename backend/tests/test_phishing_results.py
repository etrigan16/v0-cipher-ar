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

from tests.test_export import _pdf_text_tokens

from app.services.phishing.results import (
    TargetResult,
    build_target_result,
    generate_results_csv,
    summarize,
)
from app.services.reports.phishing_pdf import ExportCampaignTarget, generate_campaign_pdf

CSV_HEADERS = ["email", "name", "status", "opened", "clicked", "credential", "reported"]


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
