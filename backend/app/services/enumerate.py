"""Passive subdomain enumeration via the crt.sh CT-log API.

This module is a pure, independently-testable discovery service. It talks
only to the public crt.sh endpoint (no key required) and returns deduplicated
hostnames as a plain list. It never persists anything — persistence is the
orchestrator's job in Phase 3.

Design notes
------------
- ``http`` is injected (an ``httpx.AsyncClient``) so tests can mock the
  transport without touching the network. When omitted, a client is created
  locally and closed.
- crt.sh entries carry a ``name_value`` field that can contain several
  newline-separated names, often including a leading ``*.`` wildcard and
  sometimes unrelated sibling certificates. We filter to names that actually
  belong under the requested domain and strip wildcard/leading-dot noise.
- The source is treated as partial-failure tolerant: a timeout, HTTP error,
  or malformed body never raises. We log it and return whatever we already
  collected (which may be empty), so a scan can continue.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

# crt.sh posts results for a query without a strict limit; a generous timeout
# races against its well-known slowness rather than aborting on a first hiccup.
CRTSH_URL = "https://crt.sh"
CRTSH_TIMEOUT = 30.0


async def enumerate_subdomains(domain: str, http: httpx.AsyncClient | None = None) -> list[str]:
    """Return the deduplicated set of subdomains under ``domain`` via crt.sh.

    Args:
        domain: The apex domain to enumerate (e.g. ``example.com``). The
            ``%25.{domain}`` wildcard form is used so subdomains under the
            apex are matched.
        http: An optional ``httpx.AsyncClient`` to reuse. If omitted, a
            transient client is created for the call and closed afterwards.

    Returns:
        A list of unique hostnames discovered for the domain. Never raises:
        on a crt.sh timeout/HTTP/malformed-response error we log and return
        the (possibly empty) partial result so the enclosing scan continues.
    """
    domain = domain.strip().lower().lstrip("*.")
    query = {"q": f"%25.{domain}", "output": "json"}

    owns_client = http is None
    client = http or httpx.AsyncClient(timeout=CRTSH_TIMEOUT)
    try:
        resp = await client.get(CRTSH_URL, params=query)
        resp.raise_for_status()
        records = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException, ValueError) as exc:  # ValueError from bad JSON
        logger.warning("crt.sh enumeration failed for %s (continuing partial): %s", domain, exc)
        return []
    finally:
        if owns_client:
            await client.aclose()

    return _extract_subdomains(records, domain)


def _extract_subdomains(records: list, domain: str) -> list[str]:
    """Parse crt.sh JSON entries into unique, in-scope hostnames.

    Handles:
    - ``name_value`` holding multiple newline-separated names.
    - ``*.`` wildcard prefixes on individual names.
    - Names for other domains appearing in a cert SAN list.
    """
    found: set[str] = set()
    for entry in records or []:
        if not isinstance(entry, dict):
            continue
        name_value = entry.get("name_value") or ""
        for raw in str(name_value).splitlines():
            name = raw.strip().lower().lstrip("*.").lstrip(".")
            if _is_subdomain_of(name, domain):
                found.add(name)
    return sorted(found)


def _is_subdomain_of(name: str, domain: str) -> bool:
    """True if ``name`` equals ``domain`` or is a subdomain of it.

    ``compare_domain`` guards against suffix attacks: ``notevil.com`` must
    not match ``evil.com``.
    """
    name = name.rstrip(".")
    domain = domain.rstrip(".")
    if name == domain:
        return True
    if not name.endswith("." + domain):
        return False
    return True
