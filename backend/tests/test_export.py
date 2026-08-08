"""Phase 5 (PR 4): report export tests — CSV/PDF generators + /asm/export.

Layers:
- Unit: ``generate_csv`` / ``generate_pdf`` with plain ``ExportFinding``
  records (spec R1/R2) — no DB, no network.
- Integration: ``GET /asm/export`` over the SQLite ASGITransport client with
  the same discovery fakes as ``tests.test_asm`` (spec R3/R4).

Selective run: ``pytest tests/test_export.py -q``
"""

import base64
import csv
import io
import re
import zlib
from datetime import datetime, timezone

from app.services.reports import ExportFinding, generate_csv, generate_pdf


def _finding(**overrides) -> ExportFinding:
    """A deterministic finding record; defaults fire the missing-hsts shape."""
    fields = dict(
        asset="good.example.com",
        title="Missing Strict-Transport-Security header",
        severity="medium",
        risk_score=5.5,
        status="open",
        remediation='Enable HSTS: send "Strict-Transport-Security" on HTTPS.',
        discovered_at=datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    fields.update(overrides)
    return ExportFinding(**fields)


def _decode_pdf_stream(raw: bytes) -> bytes:
    """Decode one reportlab content stream (default: ASCII85 then Flate).

    reportlab 5.0 emits ``/Filter [ /ASCII85Decode /FlateDecode ]`` for page
    content, so the raw stream bytes are ASCII85-encoded and then
    zlib-compressed. We try the real decode first, then a bare zlib stream,
    then fall back to the raw bytes (uncompressed pages).
    """
    for decoder in (
        lambda b: zlib.decompress(base64.a85decode(b, adobe=True)),
        lambda b: zlib.decompress(b),
        lambda b: b,
    ):
        try:
            decoded = decoder(raw)
            if len(decoded) >= len(raw):  # real decompression expanded the data
                return decoded
        except Exception:
            continue
    return raw


def _pdf_text_tokens(data: bytes) -> str:
    """Extract text literals from PDF content streams (compressed or not).

    reportlab writes text as ``(token) Tj`` / ``[(t1) (t2)] TJ`` operations
    inside content streams. We decode each stream and pull every
    parenthesized literal, in order, so the joined text preserves reading
    order well enough for substring assertions.
    """
    parts: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.DOTALL):
        raw = _decode_pdf_stream(match.group(1))
        for token in re.findall(rb"\(((?:[^()\\]|\\.)*)\)", raw):
            parts.append(
                token.decode("latin-1")
                .replace(r"\(", "(")
                .replace(r"\)", ")")
                .replace(r"\\", "\\")
            )
    return " ".join(parts)


class TestCsvGenerator:
    """generate_csv — stdlib CSV, spec R1 headers, one row per finding."""

    def test_headers_match_spec(self):
        """Empty input still produces the exact spec R1 header row (no error)."""
        out = generate_csv([])
        rows = list(csv.reader(io.StringIO(out)))
        assert rows == [[
            "asset", "finding title", "severity", "risk_score",
            "status", "remediation", "discovered_at",
        ]]

    def test_one_row_per_finding_with_values(self):
        """Two findings -> header + one row each, spec-ordered values."""
        findings = [
            _finding(),
            _finding(
                asset="exposed.example.com",
                title="Exposed service on non-standard port 8443",
                severity="high",
                risk_score=8.0,
                status="resolved",
                remediation="Close the port or restrict access.",
                discovered_at=datetime(2026, 7, 2, 9, 30, 0, tzinfo=timezone.utc),
            ),
        ]
        rows = list(csv.reader(io.StringIO(generate_csv(findings))))
        assert len(rows) == 3  # header + 2 findings
        assert rows[1] == [
            "good.example.com",
            "Missing Strict-Transport-Security header",
            "medium",
            "5.5",
            "open",
            'Enable HSTS: send "Strict-Transport-Security" on HTTPS.',
            "2026-07-01T12:00:00+00:00",
        ]
        assert rows[2] == [
            "exposed.example.com",
            "Exposed service on non-standard port 8443",
            "high",
            "8",  # :g formatting drops the trailing ".0"
            "resolved",
            "Close the port or restrict access.",
            "2026-07-02T09:30:00+00:00",
        ]

    def test_escapes_commas_quotes_newlines(self):
        """Fields containing commas, quotes and newlines round-trip intact."""
        tricky = _finding(
            title='Header "X", value=1\nand a newline',
            remediation='Step 1, then step 2.\nRepeat "exactly".',
        )
        rows = list(csv.reader(io.StringIO(generate_csv([tricky]))))
        assert rows[1][1] == 'Header "X", value=1\nand a newline'
        assert rows[1][5] == 'Step 1, then step 2.\nRepeat "exactly".'

    def test_utf8_round_trips(self):
        """Non-ASCII text survives a UTF-8 encode/decode cycle."""
        finding = _finding(
            title="Certificado TLS vencido — café",
            remediation="Renovar antes del 01/01/2027 (ñandú).",
        )
        raw = generate_csv([finding]).encode("utf-8")
        assert "café".encode("utf-8") in raw
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
        assert rows[1][1] == "Certificado TLS vencido — café"
        assert rows[1][5] == "Renovar antes del 01/01/2027 (ñandú)."

    def test_unscored_finding_has_empty_risk_cell(self):
        """Legacy findings (risk_score NULL) export an empty cell, not 'None'."""
        rows = list(csv.reader(io.StringIO(generate_csv([_finding(risk_score=None)]))))
        assert rows[1][3] == ""


class TestPdfGenerator:
    """generate_pdf — reportlab A4 report, spec R2 summary + findings table."""

    def test_pdf_with_findings(self):
        """Real data -> valid %PDF with summary, distribution and scores."""
        findings = [
            _finding(),
            _finding(
                asset="exposed.example.com",
                title="Exposed service on non-standard port 8443",
                severity="medium",
                risk_score=6.5,
                status="open",
            ),
            _finding(
                asset="www.example.com",
                title="Missing X-Content-Type-Options header",
                severity="low",
                risk_score=2.5,
                status="open",
            ),
        ]
        pdf = generate_pdf(findings, "Acme Corp")
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 1000
        text = _pdf_text_tokens(pdf)
        # Title band carries the tenant name; headings + scores are present.
        assert "Acme Corp" in text
        assert "Risk Summary" in text
        assert "Top Findings" in text
        assert "6.5" in text
        assert "5.5" in text
        assert "2.5" in text
        # Summary metrics: avg = (5.5+6.5+2.5)/3 = 4.83, max = 6.5.
        assert "Average risk score: 4.83" in text
        assert "Maximum risk score: 6.5" in text

    def test_pdf_empty_tenant_zeroed_metrics(self):
        """Empty tenant -> valid %PDF with zeroed summary and a no-findings note."""
        pdf = generate_pdf([], "Acme Corp")
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 500
        text = _pdf_text_tokens(pdf)
        assert "Acme Corp" in text
        assert "Risk Summary" in text
        assert "No findings recorded" in text
        assert "Average risk score: 0.0" in text
        assert "Maximum risk score: 0.0" in text


