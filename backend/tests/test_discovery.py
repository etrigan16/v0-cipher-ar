"""Unit tests for the Phase 2 discovery services (crt.sh, DNS, fingerprint).

These tests are pure and independent: they never touch the network or the DB.
- crt.sh enumeration mocks ``httpx.AsyncClient``.
- DNS resolution mocks ``dns.resolver.Resolver``.
- fingerprinting mocks ``httpx.AsyncClient`` and monkeypatches ``ssl``/``socket``.

Selective run: ``pytest tests/test_discovery.py``
"""

import ssl

import httpx
import pytest
import pytest_asyncio

from app.services import dns as dns_service
from app.services import enumerate as crtsh
from app.services import fingerprint as fp


class _FakeResponse:
    """Minimal stand-in for httpx.Response with status/headers/text/json."""

    def __init__(self, status_code=200, headers=None, text="", json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text
        self._json = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code} error",
                request=httpx.Request("GET", "http://crt.sh"),
                response=self,
            )

    def json(self):
        return self._json


class _FakeHTTP:
    """Injected httpx.AsyncClient stand-in that returns canned responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self._closed = False

    async def get(self, url, params=None, **kwargs):
        capture = self._responses.pop(0)
        if isinstance(capture, Exception):
            raise capture
        return capture

    async def aclose(self):
        self._closed = True


class TestCrtShEnumeration:
    """crt.sh parse/dedupe + partial-failure tolerance."""

    @pytest.mark.asyncio
    async def test_enumerates_and_dedupes_subdomains(self):
        records = [
            {"name_value": "example.com\nwww.example.com\napi.example.com\n*.www.example.com"},
            {"name_value": "www.example.com"},  # duplicate across entries
            {"name_value": "notevil.com"},  # suffix-attack guard: not a subdomain
            {"name_value": "example.com"},  # apex itself
        ]
        http = _FakeHTTP([_FakeResponse(status_code=200, json_data=records)])
        result = await crtsh.enumerate_subdomains("example.com", http=http)
        assert result == ["api.example.com", "example.com", "www.example.com"]

    @pytest.mark.asyncio
    async def test_wildcard_and_leading_dots_stripped(self):
        records = [
            {"name_value": "*.foo.example.com\n..bar.example.com"},
        ]
        http = _FakeHTTP([_FakeResponse(status_code=200, json_data=records)])
        result = await crtsh.enumerate_subdomains("example.com", http=http)
        assert "foo.example.com" in result
        assert "bar.example.com" in result
        assert not any(n.startswith("*.") for n in result)

    @pytest.mark.asyncio
    async def test_crtsh_timeout_returns_partial(self):
        http = _FakeHTTP([httpx.TimeoutException("timed out")])
        result = await crtsh.enumerate_subdomains("example.com", http=http)
        assert result == []  # never raises; scan continues partial

    @pytest.mark.asyncio
    async def test_crtsh_http_error_returns_partial(self):
        http = _FakeHTTP([_FakeResponse(status_code=503, json_data=[])])
        result = await crtsh.enumerate_subdomains("example.com", http=http)
        assert result == []

    def test_extract_ignores_non_cert_records(self):
        result = crtsh._extract_subdomains([{"name_value": "x.example.com"}, "junk", None], "example.com")
        assert result == ["x.example.com"]


class _FakeAnswer:
    """Stand-in for a dns.resolver answer exposing iteration + canonical_name."""

    def __init__(self, values, canonical="example.com."):
        self._values = values
        self.canonical_name = canonical

    def __iter__(self):
        for v in self._values:
            yield _FakeRR(v)

    @property
    def response(self):
        return type("R", (), {"canonical_name": self.canonical_name})


class _FakeRR:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class _FakeResolver:
    """Canned dns.resolver.Resolver: answers by rtype, or raises."""

    def __init__(self, a=None, aaaa=None, raise_for=()):
        self._a = a
        self._aaaa = aaaa
        self._raise_for = raise_for

    def resolve(self, hostname, rtype, lifetime=None):
        if rtype in self._raise_for:
            raise _nxdomain()
        if rtype == "A" and self._a is not None:
            return _FakeAnswer(self._a, canonical=hostname + ".")
        if rtype == "AAAA" and self._aaaa is not None:
            return _FakeAnswer(self._aaaa, canonical=hostname + ".")
        raise dns_service.dns.resolver.NoAnswer()


class _nxdomain(dns_service.dns.resolver.NXDOMAIN):
    def __init__(self):
        pass


class TestDnsResolution:
    """dnspython A/AAAA resolve + NXDOMAIN/NoAnswer handling."""

    def test_resolves_a_and_aaaa(self):
        resolver = _FakeResolver(a=["203.0.113.1"], aaaa=["2001:db8::1"])
        r = dns_service.resolve("www.example.com", resolver=resolver)
        assert r.hostname == "www.example.com"
        assert r.ips == ["2001:db8::1", "203.0.113.1"]
        assert r.cname is None

    def test_nxdomain_returns_empty(self):
        resolver = _FakeResolver(raise_for=("A", "AAAA"))
        r = dns_service.resolve("missing.example.com", resolver=resolver)
        assert r.ips == []
        assert r.cname is None

    def test_noanswer_for_one_family(self):
        resolver = _FakeResolver(a=["203.0.113.1"])  # AAAA throws NoAnswer
        r = dns_service.resolve("www.example.com", resolver=resolver)
        assert r.ips == ["203.0.113.1"]

    def test_hostname_normalized(self):
        resolver = _FakeResolver(a=["203.0.113.1"])
        r = dns_service.resolve("  WWW.EXAMPLE.COM ", resolver=resolver)
        assert r.hostname == "www.example.com"


class TestHttpTlsFingerprint:
    """httpx HTTP probe + ssl TLS cert fingerprint."""

    @pytest.mark.asyncio
    async def test_full_fingerprint_dict(self, monkeypatch):
        html = "<html><head><title> Example Home </title></head></html>"
        responses = [
            _FakeResponse(
                status_code=200,
                headers={"server": "nginx", "x-powered-by": "Express"},
                text=html,
            )
        ]
        monkeypatch.setattr(fp, "_get_tls_fingerprint", lambda h, p: {"subject_cn": "*.example.com", "subject_alt_names": ["example.com"]})
        result = await fp.fingerprint("www.example.com", http=_FakeHTTP(responses))

        d = result.to_dict()
        assert d["hostname"] == "www.example.com"
        assert d["status_code"] == 200
        assert d["title"] == "Example Home"
        assert d["server"] == "nginx"
        assert d["x_powered_by"] == "Express"
        assert d["tls"]["subject_cn"] == "*.example.com"
        assert d["tls"]["subject_alt_names"] == ["example.com"]

    @pytest.mark.asyncio
    async def test_unreachable_host_never_raises(self, monkeypatch):
        responses = [httpx.ConnectError("connection refused")]
        monkeypatch.setattr(fp, "_get_tls_fingerprint", lambda h, p: None)
        result = await fp.fingerprint("down.example.com", http=_FakeHTTP(responses))
        assert result.status_code is None
        assert result.title is None
        assert result.tls is None

    def test_extract_title(self):
        assert fp._extract_title("<title>Hello &amp; Welcome</title>") == "Hello & Welcome"
        assert fp._extract_title("<html></html>") is None
        assert fp._extract_title("") is None

    def test_tls_fingerprint_from_fake_cert(self, monkeypatch):
        fake_cert = {
            "subject": ((("commonName", "api.example.com"),),),
            "subjectAltName": (("DNS", "api.example.com"), ("DNS", "www.example.com")),
        }
        assert fp._extract_tls_from_cert(fake_cert) == {
            "subject_cn": "api.example.com",
            "subject_alt_names": ["api.example.com", "www.example.com"],
        }
