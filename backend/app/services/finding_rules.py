"""Pure rule engine: turns a fingerprint into candidate findings.

Rules are pure, deterministic functions of a fingerprint dict (the shape
produced by ``FingerprintResult.to_dict()``) plus an injectable clock for the
TLS-expiry rule. They perform no I/O, so unit tests only need plain dicts.

Each fired rule yields a :class:`RuleResult` carrying the ``finding_type``,
``severity``, ``title``, ``detail`` and a deterministic ``remediation``
template. The orchestrator scores each candidate (see
``app.services.scoring.engine``) and persists the Finding row.

Rules are evaluated in a fixed order so the output is stable for a given
fingerprint (spec: deterministic finding set).
"""

import datetime
import re
from dataclasses import dataclass

# Ports that do NOT count as an exposed non-standard service.
STANDARD_PORTS = (None, 80, 443)
# ``Server: nginx/1.18.0`` leaks a version number.
_VERSION_RE = re.compile(r"\d+\.\d+")
_COOKIE_FLAG_RE = re.compile(r"\b(Secure|HttpOnly)\b", re.IGNORECASE)


@dataclass(frozen=True)
class RuleResult:
    """A candidate finding produced by a single rule."""

    finding_type: str
    severity: str  # info|low|medium|high|critical
    title: str
    detail: str
    remediation: str


def evaluate(
    fingerprint: dict,
    now: datetime.datetime | None = None,
) -> list[RuleResult]:
    """Evaluate all rules against ``fingerprint`` in a fixed order.

    Args:
        fingerprint: The dict from ``FingerprintResult.to_dict()``.
        now: The reference time for TLS-expiry. Injected for deterministic
            tests; defaults to the current UTC time.

    Returns:
        The list of fired rules (empty when nothing matches).
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    results = []
    for rule in _RULES:
        result = rule(fingerprint, now)
        if result is not None:
            results.append(result)
    return results


# --- Security header rules -------------------------------------------------


def _missing_hsts(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    if fingerprint.get("scheme") == "https" and not fingerprint.get(
        "strict_transport_security"
    ):
        return RuleResult(
            finding_type="missing-hsts",
            severity="medium",
            title="Missing Strict-Transport-Security header",
            detail=(
                "The HTTPS response does not send Strict-Transport-Security, so "
                "browsers may fall back to insecure HTTP."
            ),
            remediation=(
                "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' "
                "to every HTTPS response."
            ),
        )
    return None


def _missing_xcto(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    if fingerprint.get("scheme") == "https" and not fingerprint.get(
        "x_content_type_options"
    ):
        return RuleResult(
            finding_type="missing-xcto",
            severity="low",
            title="Missing X-Content-Type-Options header",
            detail=(
                "The HTTPS response does not send X-Content-Type-Options, allowing "
                "MIME-sniffing attacks."
            ),
            remediation=(
                "Add 'X-Content-Type-Options: nosniff' to every HTTPS response."
            ),
        )
    return None


def _missing_csp(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    if fingerprint.get("scheme") == "https" and not fingerprint.get(
        "content_security_policy"
    ):
        return RuleResult(
            finding_type="missing-csp",
            severity="medium",
            title="Missing Content-Security-Policy header",
            detail=(
                "The HTTPS response does not send a Content-Security-Policy, "
                "increasing the impact of XSS attacks."
            ),
            remediation=(
                "Add a Content-Security-Policy header restricting script and "
                "object sources."
            ),
        )
    return None


def _insecure_cookie(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    cookies = fingerprint.get("set_cookie") or []
    if any(not _is_secure_cookie(c) for c in cookies):
        return RuleResult(
            finding_type="insecure-cookie",
            severity="medium",
            title="Cookie set without Secure or HttpOnly flags",
            detail=(
                "A Set-Cookie response lacks the Secure or HttpOnly attribute, "
                "exposing the session to interception or script access."
            ),
            remediation=(
                "Set the Secure and HttpOnly flags on all cookies (e.g. "
                "Set-Cookie: session=...; Secure; HttpOnly)."
            ),
        )
    return None


# --- TLS rules -------------------------------------------------------------


def _tls_expired(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    tls = fingerprint.get("tls")
    if not tls:
        return None
    not_after = _parse_iso(tls.get("not_after"))
    if not_after is not None and not_after < now:
        return RuleResult(
            finding_type="tls-expired",
            severity="high",
            title="Expired TLS certificate",
            detail=f"The server certificate expired on {not_after.isoformat()}.",
            remediation="Renew the TLS certificate before it expires and re-issue.",
        )
    return None


def _tls_self_signed(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    tls = fingerprint.get("tls")
    if not tls:
        return None
    subject_cn = tls.get("subject_cn")
    issuer_cn = tls.get("issuer_cn")
    if subject_cn and issuer_cn and subject_cn.lower() == issuer_cn.lower():
        return RuleResult(
            finding_type="tls-self-signed",
            severity="high",
            title="Self-signed TLS certificate",
            detail=(
                "The certificate issuer matches its subject, so the chain is "
                "not trusted by clients."
            ),
            remediation=(
                "Replace the self-signed certificate with one issued by a "
                "trusted CA."
            ),
        )
    return None


def _tls_cn_mismatch(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    tls = fingerprint.get("tls")
    hostname = (fingerprint.get("hostname") or "").lower().rstrip(".")
    if not tls or not hostname:
        return None
    names = {str(n).lower().rstrip(".") for n in (tls.get("subject_alt_names") or [])}
    if tls.get("subject_cn"):
        names.add(str(tls["subject_cn"]).lower().rstrip("."))
    if any(_cert_covers_hostname(name, hostname) for name in names):
        return None
    return RuleResult(
        finding_type="tls-cn-mismatch",
        severity="high",
        title="TLS certificate hostname mismatch",
        detail=(
            f"The certificate does not cover {fingerprint.get('hostname')} — "
            "clients will reject the connection."
        ),
        remediation=(
            "Issue a certificate covering this hostname (CN or SAN entry)."
        ),
    )


# --- Port / banner rules ---------------------------------------------------


def _nonstandard_port(fingerprint: dict, now: datetime.datetime) -> RuleResult | None:
    port = fingerprint.get("port")
    if port not in STANDARD_PORTS:
        return RuleResult(
            finding_type="nonstandard-port",
            severity="medium",
            title=f"Exposed service on non-standard port {port}",
            detail=(
                f"A service answers on TCP port {port}, which is not 80/443 and "
                "may be unhardened or overlooked."
            ),
            remediation=(
                "Restrict the port to authorized clients or move the service "
                "behind the standard HTTPS front."
            ),
        )
    return None


def _server_version_disclosure(
    fingerprint: dict, now: datetime.datetime
) -> RuleResult | None:
    server = fingerprint.get("server") or ""
    if _VERSION_RE.search(server):
        return RuleResult(
            finding_type="server-version-disclosure",
            severity="low",
            title="Server version disclosed",
            detail=(
                f"The Server header ({server}) reveals a version number an "
                "attacker can match against known vulnerabilities."
            ),
            remediation=(
                "Remove version numbers from the Server header (or replace it "
                "with a generic value)."
            ),
        )
    return None


# --- Helpers ---------------------------------------------------------------


def _is_secure_cookie(value: str) -> bool:
    """A cookie is secure only when both Secure and HttpOnly are present."""
    flags = set(_COOKIE_FLAG_RE.findall(value))
    return "Secure" in flags and "HttpOnly" in flags


def _parse_iso(value) -> datetime.datetime | None:
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _cert_covers_hostname(cert_name: str, hostname: str) -> bool:
    """Exact or ``*.`` wildcard coverage of ``hostname`` by ``cert_name``."""
    if cert_name == hostname:
        return True
    if cert_name.startswith("*."):
        suffix = cert_name[1:]  # ".example.com"
        return hostname.endswith(suffix) and hostname[: -len(suffix)] != ""
    return False


# Fixed evaluation order — keeps the finding set deterministic.
_RULES = (
    _missing_hsts,
    _missing_xcto,
    _missing_csp,
    _insecure_cookie,
    _tls_expired,
    _tls_self_signed,
    _tls_cn_mismatch,
    _nonstandard_port,
    _server_version_disclosure,
)
