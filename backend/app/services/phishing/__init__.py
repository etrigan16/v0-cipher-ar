"""Phishing simulator services (Phase 2 — template renderer).

Later phases add ``tokens`` (Phase 3), ``landing`` (Phase 4) and
``results`` (Phase 5) to this package (design File Changes table).
"""

from app.services.phishing.render import render

__all__ = ["render"]
