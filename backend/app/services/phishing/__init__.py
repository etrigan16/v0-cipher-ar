"""Phishing simulator services (Phase 2+ — renderer, tokens, tracking).

Later phases add ``results`` (Phase 5) to this package (design File Changes
table). The tracking services (``landing``, ``events``) back the public
token-gated routes from Phase 4.
"""

from app.services.phishing.events import record_event
from app.services.phishing.landing import (
    credential_hash,
    is_tracking_expired,
    resolve_tracking_target,
    sha256_hex,
)
from app.services.phishing.render import render
from app.services.phishing.tokens import generate_tracking_token

__all__ = [
    "render",
    "generate_tracking_token",
    "record_event",
    "resolve_tracking_target",
    "is_tracking_expired",
    "credential_hash",
    "sha256_hex",
]
