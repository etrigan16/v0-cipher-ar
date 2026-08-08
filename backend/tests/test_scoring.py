"""Unit tests for the deterministic CVSS-like scoring engine.

Design formula: ``score = clamp(base + sum(modifiers), 0, 10)`` with
``base[severity] = {info: 0, low: 2, medium: 5, high: 8, critical: 10}`` and
per-``finding_type`` modifiers (exposed non-standard port +1.5, public TLS
issues +1.5, version disclosure +0.5, missing headers +0.5).

Bands: ``0 -> info, <4 -> low, <7 -> medium, <9 -> high, >=9 -> critical``.

Selective run: ``pytest tests/test_scoring.py``
"""

import pytest

from app.services.scoring.engine import aggregate_risk, risk_level_for, score


def _fp(**overrides) -> dict:
    fingerprint = {"hostname": "www.example.com", "port": 443, "scheme": "https"}
    fingerprint.update(overrides)
    return fingerprint


class TestBaseSeverity:
    """Base score alone (finding_type with no modifier)."""

    def test_base_mapping(self):
        expected = {
            "info": 0.0,
            "low": 2.0,
            "medium": 5.0,
            "high": 8.0,
            "critical": 10.0,
        }
        for severity, base in expected.items():
            result = score(severity, "custom-rule", _fp())
            assert result.risk_score == base
            assert result.risk_level == risk_level_for(base)

    def test_unknown_severity_scores_zero(self):
        result = score("unknown", "custom-rule", _fp())
        assert result.risk_score == 0.0
        assert result.risk_level == "info"


class TestModifiers:
    """Context modifiers stack on top of the severity base."""

    def test_exposed_nonstandard_port_adds_1_5(self):
        result = score("medium", "nonstandard-port", _fp(port=8080))
        assert result.risk_score == 6.5  # 5 + 1.5
        assert result.risk_level == "medium"

    def test_exposed_modifier_suppressed_on_standard_port(self):
        # nonstandard-port finding on a standard port: no +1.5 (base only).
        assert score("high", "nonstandard-port", _fp(port=443)).risk_score == 8.0
        assert score("high", "nonstandard-port", _fp(port=80)).risk_score == 8.0
        assert score("high", "nonstandard-port", _fp(port=None)).risk_score == 8.0

    def test_tls_issues_add_1_5(self):
        for finding_type in ("tls-expired", "tls-self-signed", "tls-cn-mismatch"):
            result = score("high", finding_type, _fp())
            assert result.risk_score == 9.5  # 8 + 1.5
            assert result.risk_level == "critical"

    def test_version_disclosure_adds_0_5(self):
        result = score("low", "server-version-disclosure", _fp())
        assert result.risk_score == 2.5  # 2 + 0.5
        assert result.risk_level == "low"

    def test_missing_headers_add_0_5(self):
        for finding_type in ("missing-hsts", "missing-csp", "missing-xcto", "insecure-cookie"):
            result = score("medium", finding_type, _fp())
            assert result.risk_score == 5.5  # 5 + 0.5
            assert result.risk_level == "medium"


class TestClamping:
    """Output is clamped to [0, 10]."""

    def test_critical_exposed_clamped_to_10(self):
        result = score("critical", "nonstandard-port", _fp(port=8080))
        assert result.risk_score == 10.0  # 10 + 1.5 clamped
        assert result.risk_level == "critical"

    def test_clamp_never_exceeds_10(self):
        # critical base + any +1.5 modifier clamps to exactly 10.0.
        assert score("critical", "tls-expired", _fp()).risk_score == 10.0
        assert score("critical", "missing-hsts", _fp()).risk_score == 10.0


class TestRiskBands:
    """Bands: 0 info, <4 low, <7 medium, <9 high, >=9 critical."""

    def test_band_boundaries(self):
        cases = [
            (0.0, "info"),
            (0.5, "low"),
            (3.9, "low"),
            (4.0, "medium"),
            (6.9, "medium"),
            (7.0, "high"),
            (8.9, "high"),
            (9.0, "critical"),
            (10.0, "critical"),
        ]
        for value, expected in cases:
            assert risk_level_for(value) == expected

    def test_band_derived_from_score(self):
        assert score("medium", "nonstandard-port", _fp(port=8080)).risk_level == "medium"  # 6.5
        assert score("high", "tls-expired", _fp()).risk_level == "critical"  # 9.5
        assert score("medium", "missing-hsts", _fp()).risk_level == "medium"  # 5.5
        assert score("high", "nonstandard-port", _fp(port=443)).risk_level == "high"  # 8.0


class TestDeterminism:
    """Same (severity, finding_type, fingerprint) -> identical result."""

    def test_deterministic_output(self):
        inputs = ("high", "tls-expired", _fp(port=8443))
        first = score(*inputs)
        second = score(*inputs)
        assert first.risk_score == second.risk_score
        assert first.risk_level == second.risk_level


class TestAggregate:
    """Asset aggregate = max of open findings; NULLs ignored; empty -> 0.0."""

    def test_max_of_open_findings(self):
        assert aggregate_risk([3.2, 7.5]) == 7.5
        assert aggregate_risk([7.5, 3.2]) == 7.5

    def test_nulls_ignored(self):
        assert aggregate_risk([None, 2.0, None]) == 2.0

    def test_empty_and_all_null_yield_zero(self):
        assert aggregate_risk([]) == 0.0
        assert aggregate_risk([None, None]) == 0.0

    def test_single_score(self):
        assert aggregate_risk([4.0]) == 4.0
