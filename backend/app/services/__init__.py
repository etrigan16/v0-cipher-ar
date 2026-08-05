"""Attack-surface discovery services (PR 2 — Discovery Services).

Pure, independently-testable modules that produce plain dict / Pydantic
results. They do NOT touch the database — persisting results is the job of
the Phase 3 orchestration layer.

Modules
-------
``enumerate``
    Passive subdomain enumeration via the crt.sh CT-log API.
``dns``
    Active DNS resolution (A/AAAA) via dnspython.
``fingerprint``
    Active HTTP/TLS fingerprinting via httpx + the standard ssl module.
"""
