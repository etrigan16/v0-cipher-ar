"""Pure scoring functions: per-finding score + asset aggregate.

This module contains no I/O. ``score`` maps (severity, finding_type,
fingerprint) to a clamped ``ScoreResult``; ``aggregate_risk`` computes the
asset-level max over open findings with NULLs treated as absent (0.0 when
none). Both are unit-tested with plain dicts (``tests/test_scoring.py``).
"""

from dataclasses import dataclass
from typing import Sequence

# Ports that do NOT count as an exposed non-standard service. Kept in sync
# with ``app.services.finding_rules.STANDARD_PORTS``.
STANDARD_PORTS = (None, 80, 443)

# Base score per severity (design.md scoring formula).
BASE_SEVERITY: dict[str, float] = {
    "info": 0.0,
    "low": 2.0,
    "medium": 5.0,
    "high": 8.0,
    "critical": 10.0,
}

# Context modifiers keyed by finding_type (design.md modifier table).
# ``nonstandard-port`` is handled separately because its modifier is
# conditional on the actual fingerprint port.
_FINDING_TYPE_MODIFIERS: dict[str, float] = {
    "tls-expired": 1.5,
    "tls-self-signed": 1.5,
    "tls-cn-mismatch": 1.5,
    "server-version-disclosure": 0.5,
    "missing-hsts": 0.5,
    "missing-csp": 0.5,
    "missing-xcto": 0.5,
    "insecure-cookie": 0.5,
}
_NONSTANDARD_PORT_DELTA = 1.5


@dataclass(frozen=True)
class ScoreResult:
    """The deterministic score and derived level for one finding."""

    risk_score: float  # clamped to [0, 10]
    risk_level: str  # info|low|medium|high|critical


def score(severity: str, finding_type: str, fingerprint: dict) -> ScoreResult:
    """Compute the clamped risk score and level for a candidate finding.

    Args:
        severity: One of ``info|low|medium|high|critical``.
        finding_type: The rule's ``finding_type`` (drives modifiers).
        fingerprint: The asset fingerprint dict (for context modifiers, e.g.
            the actual port for ``nonstandard-port``).

    Returns:
        A frozen ``ScoreResult``; never raises and never exceeds [0, 10].
    """
    base = BASE_SEVERITY.get(severity, 0.0)
    modifiers = 0.0
    if finding_type == "nonstandard-port":
        if fingerprint.get("port") not in STANDARD_PORTS:
            modifiers += _NONSTANDARD_PORT_DELTA
    else:
        modifiers += _FINDING_TYPE_MODIFIERS.get(finding_type, 0.0)

    risk_score = round(min(max(base + modifiers, 0.0), 10.0), 2)
    return ScoreResult(risk_score=risk_score, risk_level=risk_level_for(risk_score))


def risk_level_for(risk_score: float) -> str:
    """Map a clamped score to its risk band."""
    if risk_score <= 0.0:
        return "info"
    if risk_score < 4.0:
        return "low"
    if risk_score < 7.0:
        return "medium"
    if risk_score < 9.0:
        return "high"
    return "critical"


def aggregate_risk(open_scores: Sequence[float | None]) -> float:
    """Max of an asset's open findings' risk scores; 0.0 when none scored.

    NULL/absent scores are ignored (spec R3: ``Asset.risk_score`` is the max
    of open findings, 0.0 when there are none).
    """
    scored = [s for s in open_scores if s is not None]
    return round(max(scored), 2) if scored else 0.0
