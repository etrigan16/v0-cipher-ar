"""Report export generators (CSV via stdlib, PDF via reportlab — spec R1/R2).

``phishing_pdf`` (Phase 5, PR 5) adds the campaign results PDF on top of the
shared risk-scoring ``_table_style`` (design D8).
"""

from app.services.reports.generator import ExportFinding, generate_csv, generate_pdf
from app.services.reports.phishing_pdf import ExportCampaignTarget, generate_campaign_pdf

__all__ = [
    "ExportFinding",
    "generate_csv",
    "generate_pdf",
    "ExportCampaignTarget",
    "generate_campaign_pdf",
]
