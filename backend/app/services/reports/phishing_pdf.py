"""Phishing campaign results PDF generator (Phase 5, PR 5).

Reuses the risk-scoring reportlab stack — the shared ``_table_style`` from
``app.services.reports.generator`` (design D8) — so campaign PDFs share the
dark-header/zebra look without duplicating it. Pure: the route passes a
campaign-like object and ``ExportCampaignTarget`` rows and receives ``bytes``
back; no I/O, no DB (same contract as ``generate_pdf``).
"""

import io
from dataclasses import dataclass
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.reports.generator import _table_style

# Dark title band palette — matches the risk-scoring report look.
_HEADER_BG = colors.HexColor("#1F2937")
_HEADER_FG = colors.white


@dataclass(frozen=True)
class ExportCampaignTarget:
    """Minimal per-target row consumed by the PDF generator (ORM-free).

    ``reported`` feeds the summary stats section; the per-target table shows
    email, status, opened, clicked and credentials (PR-5 spec).
    """

    email: str
    name: str
    status: str
    opened: bool
    clicked: bool
    credential: bool
    reported: bool = False


def _percent(part: int, whole: int) -> str:
    """Percentage string; 0% when the denominator is empty (spec R2/R3)."""
    return f"{round(part / whole * 100, 2):g}%" if whole else "0%"


def _yes_no(flag: bool) -> str:
    return "Yes" if flag else "No"


def generate_campaign_pdf(campaign, targets: Sequence[ExportCampaignTarget]) -> bytes:
    """Render an A4 campaign results PDF (spec R3 / PR-5 export).

    Layout: dark title band with the campaign name, a Results Summary section
    (total, sent, opened/clicked with rates, credentials, reported) and a
    per-target table (email, status, opened, clicked, credentials). Summary
    stats are derived from the same rows rendered below; an empty campaign
    produces zeroed stats and a no-targets note.

    ``campaign`` is duck-typed (``.name``, ``.status``) so the generator
    stays free of the ORM — the route passes the ORM ``Campaign`` directly.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
        title=f"{campaign.name} - Phishing Campaign Results",
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

    total = len(targets)
    sent = sum(1 for t in targets if t.status == "active")
    opened = sum(1 for t in targets if t.opened)
    clicked = sum(1 for t in targets if t.clicked)
    credentials = sum(1 for t in targets if t.credential)
    reported = sum(1 for t in targets if t.reported)

    story = []

    # Dark title band.
    title_band = Table(
        [[Paragraph(f"{campaign.name} - Phishing Campaign Results", title_style)]],
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

    # Results summary.
    story.append(Paragraph("Results Summary", h2_style))
    story.append(Spacer(1, 3 * mm))
    summary_rows = [
        ["Total targets", str(total)],
        ["Sent (active)", str(sent)],
        ["Opened", f"{opened} ({_percent(opened, sent)})"],
        ["Clicked", f"{clicked} ({_percent(clicked, sent)})"],
        ["Credentials", str(credentials)],
        ["Reported", str(reported)],
    ]
    summary_table = Table(summary_rows, colWidths=[50 * mm, 40 * mm])
    summary_table.setStyle(_table_style())
    story.append(summary_table)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(f"Campaign status: {campaign.status}", body_style))
    story.append(Spacer(1, 6 * mm))

    # Per-target table.
    story.append(Paragraph("Per-Target Results", h2_style))
    story.append(Spacer(1, 3 * mm))
    table_data: list[list] = [
        [
            Paragraph("Email", th_style),
            Paragraph("Status", th_style),
            Paragraph("Opened", th_style),
            Paragraph("Clicked", th_style),
            Paragraph("Credentials", th_style),
        ]
    ]
    if targets:
        for target in targets:
            table_data.append(
                [
                    Paragraph(target.email, cell_style),
                    target.status,
                    _yes_no(target.opened),
                    _yes_no(target.clicked),
                    _yes_no(target.credential),
                ]
            )
    else:
        table_data.append(
            [Paragraph("No targets recorded for this campaign.", cell_style), "", "", "", ""]
        )
    targets_table = Table(
        table_data,
        colWidths=[58 * mm, 24 * mm, 22 * mm, 22 * mm, 30 * mm],
        repeatRows=1,
    )
    targets_table.setStyle(_table_style())
    story.append(targets_table)

    doc.build(story)
    return buffer.getvalue()
