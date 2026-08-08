"""Deterministic CVSS-like scoring engine.

Design formula (design.md, Decision D2):

    score = clamp(base + sum(modifiers), 0, 10)

``base[severity] = {info: 0, low: 2, medium: 5, high: 8, critical: 10}`` and
per-``finding_type`` modifiers: an exposed non-standard port (+1.5), public
TLS issues (expired / self-signed / CN mismatch, +1.5), server version
disclosure (+0.5) and missing security headers (+0.5).

``risk_level`` bands: ``0 -> info, <4 -> low, <7 -> medium, <9 -> high,
>=9 -> critical``.

Everything here is pure: ``score`` depends only on its inputs, so identical
(severity, finding_type, fingerprint) inputs produce identical output.
"""

from app.services.scoring.engine import (
    ScoreResult,
    aggregate_risk,
    risk_level_for,
    score,
)

__all__ = ["ScoreResult", "aggregate_risk", "risk_level_for", "score"]
