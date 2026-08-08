"""Report export generators: CSV via the stdlib, PDF via reportlab.

Design D5: reportlab is pure-Python and slim-Docker-safe. Both generators
are pure functions of the findings list — no I/O, no DB access — which keeps
them unit-testable with plain ``ExportFinding`` records (spec R1/R2).

Public API (re-exported from the package ``app.services.reports``):
``ExportFinding``, ``generate_csv``, ``generate_pdf``.
"""

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Spec R1 CSV headers — order fixed by design.md Export section.
CSV_HEADERS = (
    "asset",
    "finding title",
    "severity",
    "risk_score",
    "status",
    "remediation",
    "discovered_at",
)

# Severity bands — the full key set so empty tenants still render zeroed
# counts (mirrors ``app.routes.asm.SEVERITIES``).
SEVERITIES = ("info", "low", "medium", "high", "critical")

# Dark header palette: slate-800 header rows with white text, light zebra
# rows below (professional A4 look without a theme dependency).
_HEADER_BG = colors.HexColor("#1F2937")
_HEADER_FG = colors.white
_ALT_ROW_BG = colors.HexColor("#F3F4F6")
_GRID_COLOR = colors.HexColor("#D1D5DB")


@dataclass(frozen=True)
class ExportFinding:
    """Minimal finding record consumed by the report generators.

    The route builds these from a tenant-scoped ``Finding``/``Asset`` join so
    the generators stay free of DB and ORM imports (design: pure-Python).
    """

    asset: str
    title: str
    severity: str
    risk_score: float | None
    status: str
    remediation: str | None
    discovered_at: datetime


def _fmt_number(value: float | None) -> str:
    """Render a score without a trailing ``.0``; empty string for NULL."""
    return "" if value is None else f"{value:g}"


def _fmt_datetime(value) -> str:
    """ISO-8601 with second precision; tolerates naive or aware datetimes."""
    if hasattr(value, "isoformat"):
        return value.isoformat(timespec="seconds")
    return str(value)


def generate_csv(findings: Iterable[ExportFinding]) -> str:
    """Render findings as CSV (spec R1): headers + one row per finding.

    Uses the stdlib ``csv`` module so quoting/escaping of commas, quotes and
    newlines is handled correctly; newlines are normalized to ``\\n`` for
    deterministic, cross-platform output. Returns headers only when
    ``findings`` is empty (spec: headers-only CSV, never an error).
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_HEADERS)
    for finding in findings:
        writer.writerow(
            [
                finding.asset,
                finding.title,
                finding.severity,
                _fmt_number(finding.risk_score),
                finding.status,
                finding.remediation or "",
                _fmt_datetime(finding.discovered_at),
            ]
        )
    return buffer.getvalue()


def generate_pdf(findings: Sequence[ExportFinding], tenant_name: str) -> bytes:
    """Render an A4 executive PDF report (spec R2).

    Layout: dark title band with the tenant name, a Risk Summary section
    (severity distribution, average and maximum risk) and a findings table
    sorted by risk (desc) whose columns include remediation. Empty tenants
    produce the same structure with zeroed metrics and a no-findings note.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
        title=f"{tenant_name} - Attack Surface Executive Report",
        author="Aukalabs",
    )

    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitleBand",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=_HEADER_FG,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceAfter=4,
        textColor=colors.HexColor("#111827"),
    )
    th_style = ParagraphStyle(
        "ReportTH",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=_HEADER_FG,
    )
    cell_style = ParagraphStyle(
        "ReportCell",
        parent=base["Normal"],
        fontSize=8,
        leading=10,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=base["Normal"],
        fontSize=10,
        leading=13,
    )

    story = []

    # Dark title band.
    title_band = Table(
        [[Paragraph(f"{tenant_name} - Attack Surface Executive Report", title_style)]],
        colWidths=[doc.width],
    )
    title_band.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _HEADER_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(title_band)
    story.append(Spacer(1, 6 * mm))

    # Risk summary: severity distribution (full 5-key shape) + avg/max.
    counts = {sev: 0 for sev in SEVERITIES}
    scored: list[float] = []
    for finding in findings:
        if finding.severity in counts:
            counts[finding.severity] += 1
        if finding.risk_score is not None:
            scored.append(finding.risk_score)
    avg_risk = round(sum(scored) / len(scored), 2) if scored else 0.0
    max_risk = round(max(scored), 2) if scored else 0.0

    story.append(Paragraph("Risk Summary", h2_style))
    story.append(Spacer(1, 3 * mm))
    severity_rows = [["Severity", "Findings"]] + [
        [sev, str(counts[sev])] for sev in SEVERITIES
    ]
    severity_table = Table(severity_rows, colWidths=[50 * mm, 40 * mm])
    severity_table.setStyle(_table_style())
    story.append(severity_table)
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            f"Average risk score: {avg_risk}  ·  Maximum risk score: {max_risk}",
            body_style,
        )
    )
    story.append(Spacer(1, 6 * mm))

    # Findings table sorted by risk desc (unscored findings trail last).
    story.append(Paragraph("Top Findings", h2_style))
    story.append(Spacer(1, 3 * mm))
    ordered = sorted(
        findings,
        key=lambda f: (f.risk_score if f.risk_score is not None else -1.0, f.title),
        reverse=True,
    )
    table_data: list[list] = [
        [
            Paragraph("Severity", th_style),
            Paragraph("Risk Score", th_style),
            Paragraph("Title", th_style),
            Paragraph("Asset", th_style),
            Paragraph("Status", th_style),
            Paragraph("Remediation", th_style),
        ]
    ]
    if ordered:
        for finding in ordered:
            table_data.append(
                [
                    finding.severity,
                    _fmt_number(finding.risk_score),
                    Paragraph(finding.title, cell_style),
                    finding.asset,
                    finding.status,
                    Paragraph(finding.remediation or "", cell_style),
                ]
            )
    else:
        table_data.append(
            [Paragraph("No findings recorded for this tenant.", cell_style), "", "", "", "", ""]
        )
    findings_table = Table(
        table_data,
        colWidths=[18 * mm, 18 * mm, 40 * mm, 32 * mm, 18 * mm, 56 * mm],
        repeatRows=1,
    )
    findings_table.setStyle(_table_style())
    story.append(findings_table)

    doc.build(story)
    return buffer.getvalue()


def _table_style() -> TableStyle:
    """Shared table look: dark header row, white bold text, zebra body rows."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _HEADER_FG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, _GRID_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW_BG]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
