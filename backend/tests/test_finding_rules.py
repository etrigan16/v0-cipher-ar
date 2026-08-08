"""Unit tests for the pure rule engine (``app.services.finding_rules``).

Rules transform a fingerprint dict (as produced by
``FingerprintResult.to_dict()``) into candidate findings. They are pure and
deterministic: no I/O, and a fixed injected ``now`` makes the TLS-expiry rule
fully deterministic.

Selective run: ``pytest tests/test_finding_rules.py``
"""

import datetime

import pytest

from app.services import finding_rules as rules

NOW = datetime.datetime(2026, 8, 8, tzinfo=datetime.timezone.utc)


def _base_fingerprint(**overrides) -> dict:
    """A healthy fingerprint that matches NO rule; tests mutate one field."""
    fingerprint = {
        "hostname": "www.example.com",
        "port": 443,
        "scheme": "https",
        "status_code": 200,
        "title": "Example",
        "server": "nginx",
        "x_powered_by": None,
        "strict_transport_security": "max-age=31536000",
        "x_content_type_options": "nosniff",
        "content_security_policy": "default-src 'self'",
        "set_cookie": ["session=abc; Secure; HttpOnly"],
        "tls": {
            "subject_cn": "www.example.com",
            "issuer_cn": "Let's Encrypt",
            "subject_alt_names": ["www.example.com"],
            "not_before": "2026-01-01T00:00:00Z",
            "not_after": "2027-01-01T00:00:00Z",
        },
    }
    fingerprint.update(overrides)
    return fingerprint


def _types(results: list) -> list[str]:
    return [r.finding_type for r in results]


class TestMissingSecurityHeaders:
    """missing-hsts / missing-xcto / missing-csp fire only on https w/o header."""

    def test_hsts_missing_fires_medium(self):
        fp = _base_fingerprint(strict_transport_security=None)
        results = rules.evaluate(fp, now=NOW)
        assert _types(results) == ["missing-hsts"]
        assert results[0].severity == "medium"
        assert results[0].title

    def test_hsts_present_or_http_no_fire(self):
        present = rules.evaluate(_base_fingerprint(), now=NOW)
        http = rules.evaluate(
            _base_fingerprint(scheme="http", strict_transport_security=None), now=NOW
        )
        assert "missing-hsts" not in _types(present)
        assert "missing-hsts" not in _types(http)

    def test_xcto_missing_fires_low(self):
        fp = _base_fingerprint(x_content_type_options=None)
        results = rules.evaluate(fp, now=NOW)
        assert "missing-xcto" in _types(results)
        assert next(r for r in results if r.finding_type == "missing-xcto").severity == "low"

    def test_csp_missing_fires_medium(self):
        fp = _base_fingerprint(content_security_policy=None)
        results = rules.evaluate(fp, now=NOW)
        assert "missing-csp" in _types(results)
        assert next(r for r in results if r.finding_type == "missing-csp").severity == "medium"


class TestInsecureCookie:
    """insecure-cookie fires when a Set-Cookie lacks Secure or HttpOnly."""

    def test_cookie_without_secure_fires(self):
        fp = _base_fingerprint(set_cookie=["session=abc; HttpOnly"])
        results = rules.evaluate(fp, now=NOW)
        assert "insecure-cookie" in _types(results)
        assert next(r for r in results if r.finding_type == "insecure-cookie").severity == "medium"

    def test_cookie_without_httponly_fires(self):
        fp = _base_fingerprint(set_cookie=["session=abc; Secure"])
        assert "insecure-cookie" in _types(rules.evaluate(fp, now=NOW))

    def test_secure_httponly_cookie_no_fire(self):
        fp = _base_fingerprint(set_cookie=["session=abc; Secure; HttpOnly"])
        assert "insecure-cookie" not in _types(rules.evaluate(fp, now=NOW))

    def test_no_cookie_no_fire(self):
        fp = _base_fingerprint(set_cookie=None)
        assert "insecure-cookie" not in _types(rules.evaluate(fp, now=NOW))


class TestTlsRules:
    """tls-expired / tls-self-signed / tls-cn-mismatch."""

    def test_expired_cert_fires_high(self):
        fp = _base_fingerprint(
            tls={
                "subject_cn": "www.example.com",
                "issuer_cn": "Let's Encrypt",
                "subject_alt_names": ["www.example.com"],
                "not_before": "2025-01-01T00:00:00Z",
                "not_after": "2026-01-01T00:00:00Z",  # < NOW
            }
        )
        results = rules.evaluate(fp, now=NOW)
        assert "tls-expired" in _types(results)
        assert next(r for r in results if r.finding_type == "tls-expired").severity == "high"

    def test_valid_cert_no_expiry_fire(self):
        fp = _base_fingerprint()  # not_after 2027 > NOW
        assert "tls-expired" not in _types(rules.evaluate(fp, now=NOW))

    def test_self_signed_fires_high(self):
        fp = _base_fingerprint(
            tls={
                "subject_cn": "www.example.com",
                "issuer_cn": "www.example.com",  # same CN -> self-signed
                "subject_alt_names": ["www.example.com"],
                "not_before": "2026-01-01T00:00:00Z",
                "not_after": "2027-01-01T00:00:00Z",
            }
        )
        results = rules.evaluate(fp, now=NOW)
        assert "tls-self-signed" in _types(results)
        assert next(r for r in results if r.finding_type == "tls-self-signed").severity == "high"

    def test_ca_issued_cert_no_self_signed_fire(self):
        fp = _base_fingerprint()  # issuer "Let's Encrypt" != subject
        assert "tls-self-signed" not in _types(rules.evaluate(fp, now=NOW))

    def test_cn_mismatch_fires_when_hostname_uncovered(self):
        fp = _base_fingerprint(
            hostname="api.example.com",
            tls={
                "subject_cn": "www.example.com",
                "issuer_cn": "Let's Encrypt",
                "subject_alt_names": ["www.example.com"],
                "not_before": "2026-01-01T00:00:00Z",
                "not_after": "2027-01-01T00:00:00Z",
            },
        )
        results = rules.evaluate(fp, now=NOW)
        assert "tls-cn-mismatch" in _types(results)
        assert next(r for r in results if r.finding_type == "tls-cn-mismatch").severity == "high"

    def test_wildcard_subject_covers_hostname_no_fire(self):
        fp = _base_fingerprint(
            hostname="www.example.com",
            tls={
                "subject_cn": "*.example.com",
                "issuer_cn": "Let's Encrypt",
                "subject_alt_names": ["example.com"],
                "not_before": "2026-01-01T00:00:00Z",
                "not_after": "2027-01-01T00:00:00Z",
            },
        )
        assert "tls-cn-mismatch" not in _types(rules.evaluate(fp, now=NOW))

    def test_san_covers_hostname_no_fire(self):
        fp = _base_fingerprint(
            hostname="api.example.com",
            tls={
                "subject_cn": "example.com",
                "issuer_cn": "Let's Encrypt",
                "subject_alt_names": ["api.example.com", "www.example.com"],
                "not_before": "2026-01-01T00:00:00Z",
                "not_after": "2027-01-01T00:00:00Z",
            },
        )
        assert "tls-cn-mismatch" not in _types(rules.evaluate(fp, now=NOW))


class TestPortAndServer:
    """nonstandard-port and server-version-disclosure."""

    def test_nonstandard_port_fires_medium(self):
        fp = _base_fingerprint(port=8080)
        results = rules.evaluate(fp, now=NOW)
        assert "nonstandard-port" in _types(results)
        assert next(r for r in results if r.finding_type == "nonstandard-port").severity == "medium"

    def test_standard_ports_no_fire(self):
        for port in (None, 80, 443):
            assert "nonstandard-port" not in _types(rules.evaluate(_base_fingerprint(port=port), now=NOW))

    def test_server_version_disclosure_fires_low(self):
        fp = _base_fingerprint(server="nginx/1.18.0")
        results = rules.evaluate(fp, now=NOW)
        assert "server-version-disclosure" in _types(results)
        assert next(r for r in results if r.finding_type == "server-version-disclosure").severity == "low"

    def test_server_without_version_no_fire(self):
        fp = _base_fingerprint(server="nginx")
        assert "server-version-disclosure" not in _types(rules.evaluate(fp, now=NOW))


class TestEngineProperties:
    """Determinism, empty result, and fixed rule ordering."""

    def test_clean_fingerprint_produces_no_findings(self):
        assert rules.evaluate(_base_fingerprint(), now=NOW) == []

    def test_deterministic_output(self):
        fp = _base_fingerprint(
            strict_transport_security=None,
            content_security_policy=None,
            port=8443,
            server="Apache/2.4.41",
            set_cookie=["sid=1"],
        )
        first = rules.evaluate(fp, now=NOW)
        second = rules.evaluate(fp, now=NOW)
        assert [(r.finding_type, r.severity, r.title) for r in first] == [
            (r.finding_type, r.severity, r.title) for r in second
        ]
        # Every candidate carries a remediation template for the orchestrator.
        assert all(r.remediation for r in first)

    def test_rules_fire_in_fixed_order(self):
        fp = _base_fingerprint(
            strict_transport_security=None,
            x_content_type_options=None,
            content_security_policy=None,
            set_cookie=["sid=1"],
            port=8080,
            server="nginx/1.24.0",
            tls={
                "subject_cn": "www.example.com",
                "issuer_cn": "www.example.com",
                "subject_alt_names": ["www.example.com"],
                "not_before": "2025-01-01T00:00:00Z",
                "not_after": "2026-01-01T00:00:00Z",
            },
        )
        results = rules.evaluate(fp, now=NOW)
        assert _types(results) == [
            "missing-hsts",
            "missing-xcto",
            "missing-csp",
            "insecure-cookie",
            "tls-expired",
            "tls-self-signed",
            "nonstandard-port",
            "server-version-disclosure",
        ]
