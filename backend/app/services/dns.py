"""Active DNS resolution (A/AAAA) via dnspython.

A pure, independently-testable discovery module. It resolves a hostname to
its set of IPv4/IPv6 addresses and reports NXDOMAIN / other lookup failures
without raising, so enumeration can skip unresolvable hosts and keep going.

Design notes
------------
- ``resolver`` is injected (a ``dns.resolver.Resolver``) so tests can pass a
  stub that returns canned answers or raises ``dns.resolver.NXDOMAIN``,
  without touching the network. When omitted a real resolver is created.
- Each query carries an explicit per-query timeout so slow or unresponsive
  nameservers cannot stall a scan indefinitely.
- A hostname with no records of a given type (``NoAnswer``) is not an error —
  we just return an empty list for that family and continue with the other.
- Returns a plain ``ResolutionResult`` object (lightweight, Pydantic-free)
  so consumers get typed fields without coupling to the persistence layer.
"""

import logging

import dns.exception
import dns.resolver

logger = logging.getLogger(__name__)

# Seconds per DNS query. Bounded and conservative: DNS should be fast; if a
# resolver is slow we prefer skipping the host over blocking the scan.
QUERY_TIMEOUT = 5.0


class ResolutionResult:
    """The outcome of resolving a hostname.

    Attributes:
        hostname: The hostname that was queried.
        ips: The set of unique IP addresses (v4 + v6) resolved for it.
        cname: The resolved CNAME target, if one was found (``None`` otherwise).
    """

    def __init__(self, hostname: str, ips: list[str], cname: str | None = None):
        self.hostname = hostname
        self.ips = ips
        self.cname = cname

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"ResolutionResult(hostname={self.hostname!r}, ips={self.ips!r}, cname={self.cname!r})"


def resolve(
    hostname: str,
    resolver: dns.resolver.Resolver | None = None,
    timeout: float = QUERY_TIMEOUT,
) -> ResolutionResult:
    """Resolve ``hostname`` to its A and AAAA addresses using dnspython.

    Args:
        hostname: The host to resolve.
        resolver: An optional ``dns.resolver.Resolver`` to use. If omitted a
            real resolver is created.
        timeout: Per-query timeout in seconds (default ``QUERY_TIMEOUT``).

    Returns:
        A ``ResolutionResult`` with the unique ``ips``. NXDOMAIN, NoAnswer,
        and timeout conditions do not raise — they yield an empty ``ips``
        list so callers can skip the host and continue.
    """
    hostname = hostname.strip().lower()
    own = resolver is None
    r: dns.resolver.Resolver = resolver or dns.resolver.Resolver()

    ips: set[str] = set()
    cname: str | None = None

    for rtype in ("A", "AAAA"):
        try:
            answers = r.resolve(hostname, rtype, lifetime=timeout)
            for answer in answers:
                ips.add(str(answer))
            # A/AAAA answers carry a possible CNAME via response.canonical_name
            if getattr(answers, "response", None) is not None and cname is None:
                canon = answers.response.canonical_name
                canon_str = str(canon).rstrip(".").lower()
                if canon_str and canon_str != hostname:
                    cname = canon_str
        except dns.resolver.NXDOMAIN:
            logger.info("DNS NXDOMAIN for %s (%s)", hostname, rtype)
            return ResolutionResult(hostname=hostname, ips=[], cname=None)
        except dns.resolver.NoAnswer:
            # Hostname exists but has no record of this type — not an error.
            logger.debug("DNS NoAnswer for %s (%s)", hostname, rtype)
            continue
        except (
            dns.exception.Timeout,
            dns.resolver.NoNameservers,
            dns.resolver.LifetimeTimeout,
        ) as exc:
            logger.warning("DNS %s lookup failed for %s: %s", rtype, hostname, exc)
            continue

    return ResolutionResult(hostname=hostname, ips=sorted(ips), cname=cname)
