"""LLM enrichment package (Phase 4 — PR 3).

Optional-key OpenAI-compatible client pointed at Groq (ADR-005); degrades to
deterministic templates when no key is configured or the call fails.
"""

from app.services.llm.enrich import (
    EnrichmentResult,
    enrich_finding,
    enrich_scan_findings,
)

__all__ = ["EnrichmentResult", "enrich_finding", "enrich_scan_findings"]
