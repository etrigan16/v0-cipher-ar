"""Attack-surface discovery services (PR 2 + PR 3).

The pure Phase 2 modules (``enumerate``, ``dns``, ``fingerprint``) produce
plain dict / Pydantic results and never touch the database. ``orchestrator``
(Phase 3) wires those pure services into DB persistence and owns the ``Scan``
lifecycle.

Modules
-------
``enumerate``
    Passive subdomain enumeration via the crt.sh CT-log API.
``dns``
    Active DNS resolution (A/AAAA) via dnspython.
``fingerprint``
    Active HTTP/TLS fingerprinting via httpx + the standard ssl module.
``orchestrator``
    ``run_scan`` — Scan lifecycle, Asset upsert, Finding persistence.
"""
