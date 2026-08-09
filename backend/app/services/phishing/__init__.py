"""Phishing simulator services (Phase 2+ — renderer, tokens).

Later phases add ``landing`` (Phase 4) and ``results`` (Phase 5) to this
package (design File Changes table).
"""

from app.services.phishing.render import render
from app.services.phishing.tokens import generate_tracking_token

__all__ = ["render", "generate_tracking_token"]
