"""Active HTTP/TLS fingerprinting via httpx + standard ssl.

A pure, independently-testable discovery module. It probes a live host with
an HTTP GET (capturing status code, key headers and the HTML title) and, when
the port speaks TLS, reads the peer certificate's subject CN and SAN entries.

Both sources are optional and best-effort: an unreachable HTTP endpoint or a
non-TLS port should not abort the caller. We return a typed result dict plus
a small list of candidate findings for the orchestrator to persist (Phase 3).

We deliberately do NOT build sockets/transports ourselves beyond a bounded
``ssl`` connection: everything is synchronous and short-lived so the results
are trivially unit-testable by faking ``http`` and ``ssl``.
"""

import logging
import re
import socket
import ssl
from html import unescape

import httpx

logger = logging.getLogger(__name__)

# Default HTTP probe target. Port 443 + https is the common case for a host
# discovered by crt.sh, but callers can override.
DEFAULT_PORT = 443
DEFAULT_SCHEME = "https"
HTTP_TIMEOUT = 10.0
TLS_TIMEOUT = 5.0

# Headers we capture verbatim from the HTTP response (lowercased keys).
CAPTURED_HEADERS = ("server", "x-powered-by")

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


class FingerprintResult:
    """The HTTP/TLS fingerprint of a scored host.

    Attributes:
        hostname: The host that was probed.
        port: The port that was probed.
        scheme: The URL scheme used (``http`` or ``https``).
        status_code: The HTTP status code, or ``None`` if the probe failed.
        title: The HTML ``<title>`` text (unescaped), or ``None``.
        server: The value of the ``Server`` header, or ``None``.
        x_powered_by: The value of the ``X-Powered-By`` header, or ``None``.
        tls: A dict with ``subject_cn`` and ``subject_alt_names`` from the TLS
            peer certificate, or ``None`` if TLS negotiation did not occur.
        findings: Candidate findings (list of dicts) for the orchestrator to
            persist, e.g. ``{"severity": ..., "title": ..., "detail": ...}``.
    """

    def __init__(
        self,
        hostname: str,
        port: int = DEFAULT_PORT,
        scheme: str = DEFAULT_SCHEME,
        status_code: int | None = None,
        title: str | None = None,
        server: str | None = None,
        x_powered_by: str | None = None,
        tls: dict | None = None,
        findings: list[dict] | None = None,
    ):
        self.hostname = hostname
        self.port = port
        self.scheme = scheme
        self.status_code = status_code
        self.title = title
        self.server = server
        self.x_powered_by = x_powered_by
        self.tls = tls
        self.findings = findings or []

    def to_dict(self) -> dict:
        """Serialize to a plain dict suitable for an ``Asset`` fingerprint JSON."""
        return {
            "hostname": self.hostname,
            "port": self.port,
            "scheme": self.scheme,
            "status_code": self.status_code,
            "title": self.title,
            "server": self.server,
            "x_powered_by": self.x_powered_by,
            "tls": self.tls,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"FingerprintResult(hostname={self.hostname!r}, status={self.status_code!r})"


async def fingerprint(
    hostname: str,
    port: int = DEFAULT_PORT,
    scheme: str = DEFAULT_SCHEME,
    http: httpx.AsyncClient | None = None,
) -> FingerprintResult:
    """Fingerprint ``hostname`` over HTTP(S) and, when applicable, TLS.

    Args:
        hostname: The host to probe.
        port: The TCP port to probe (default 443).
        scheme: ``http`` or ``https`` (default ``https``).
        http: An optional ``httpx.AsyncClient`` to reuse. If omitted a
            transient client is created for the call and closed afterwards.

    Returns:
        A ``FingerprintResult``. Network errors never raise — they are logged
        and reflected as ``None`` fields so the caller can continue.
    """
    hostname = hostname.strip().lower().rstrip(".")
    result = FingerprintResult(hostname=hostname, port=port, scheme=scheme)

    if scheme == "https":
        result.tls = _get_tls_fingerprint(hostname, port)

    own_client = http is None
    client = http or httpx.AsyncClient(timeout=HTTP_TIMEOUT, verify=False)
    try:
        url = f"{scheme}://{hostname}"
        if port not in (None, 80, 443):
            url = f"{scheme}://{hostname}:{port}"
        resp = await client.get(url, follow_redirects=True)
        result.status_code = resp.status_code
        for header in CAPTURED_HEADERS:
            value = resp.headers.get(header)
            if header == "x-powered-by":
                result.x_powered_by = value
            else:
                result.server = value
        result.title = _extract_title(resp.text)
    except (httpx.HTTPError, httpx.TimeoutException, ValueError) as exc:
        logger.warning("HTTP fingerprint failed for %s:%s (%s): %s", hostname, port, scheme, exc)
    finally:
        if own_client:
            await client.aclose()

    return result


def get_fingerprint(
    hostname: str,
    port: int = DEFAULT_PORT,
    scheme: str = DEFAULT_SCHEME,
    http: httpx.AsyncClient | None = None,
) -> FingerprintResult:
    """Synchronous convenience wrapper around :func:`fingerprint`.

    Useful for quick one-off probes or sync call paths. Prefer ``await
    fingerprint(...)`` in async workflows.
    """
    import asyncio

    return asyncio.run(fingerprint(hostname=hostname, port=port, scheme=scheme, http=http))


def _get_tls_fingerprint(hostname: str, port: int) -> dict | None:
    """Fetch the peer certificate CN and SANs of a TLS connection.

    Returns ``None`` when the port is not TLS (e.g. plain HTTP on 80) or when
    the connection fails, so callers are not blocked by a missing cert.
    """
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with socket.create_connection((hostname, port), timeout=TLS_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
        if not cert:
            return None
        return _extract_tls_from_cert(cert)
    except (ssl.SSLError, ssl.CertificateError, OSError, ValueError) as exc:
        logger.warning("TLS fingerprint failed for %s:%s: %s", hostname, port, exc)
        return None


def _extract_tls_from_cert(cert: dict) -> dict:
    """Extract ``subject_cn`` and sorted ``subject_alt_names`` from a cert dict.

    Split out from the socket logic so it is unit-testable with a canned
    certificate without opening any connection.
    """
    subject_cn = None
    for part in cert.get("subject", ()):  # list of ((key, value), ...)
        for key, value in part:
            if key == "commonName":
                subject_cn = value
    san = set()
    for entry in cert.get("subjectAltName", ()):  # (type, value) pairs
        san.add(str(entry[1]))
    return {
        "subject_cn": subject_cn,
        "subject_alt_names": sorted(san),
    }


def _extract_title(html: str) -> str | None:
    """Pull and unescape the ``<title>`` text from an HTML body.

    Returns ``None`` when there is no title tag.
    """
    if not html:
        return None
    match = _TITLE_RE.search(html)
    if not match:
        return None
    return unescape(match.group(1)).strip() or None
