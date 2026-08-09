"""Phishing simulator services — renderer, tokens, tracking, results (Phase 5).

The tracking services (``landing``, ``events``) back the public token-gated
routes from Phase 4; the results service (``results``) computes the
tenant-scoped per-target and aggregate stats surfaced by the Phase 5 routes.
"""

from app.services.phishing.events import record_event
from app.services.phishing.landing import (
    credential_hash,
    is_tracking_expired,
    resolve_tracking_target,
    sha256_hex,
)
from app.services.phishing.render import render
from app.services.phishing.results import (
    ResultsSummary,
    TargetResult,
    build_target_result,
    generate_results_csv,
    summarize,
)
from app.services.phishing.tokens import generate_tracking_token

__all__ = [
    "render",
    "generate_tracking_token",
    "record_event",
    "resolve_tracking_target",
    "is_tracking_expired",
    "credential_hash",
    "sha256_hex",
    "TargetResult",
    "ResultsSummary",
    "build_target_result",
    "summarize",
    "generate_results_csv",
]
