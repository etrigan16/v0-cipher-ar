"""Tracking token generation (design D1).

Per-target ``secrets.token_urlsafe(16)`` tokens are assigned at campaign
launch (spec R4). 128 bits of entropy plus the unique index on
``Target.tracking_token`` (spec R3) make collisions practically impossible
across all campaigns.
"""

import secrets


def generate_tracking_token() -> str:
    """Return a cryptographically random, URL-safe tracking token.

    ``token_urlsafe(16)`` encodes 16 random bytes as unpadded base64
    (22 characters from ``A-Za-z0-9_-``) — safe in URLs, query strings,
    and filenames without further escaping.
    """
    return secrets.token_urlsafe(16)
