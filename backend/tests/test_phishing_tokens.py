"""Tracking token generator unit tests (Phishing Simulator — Phase 3, PR 3).

Covers design D1: per-target ``secrets.token_urlsafe(16)`` tokens, unique
across all campaigns, assigned at launch (spec R3/R4). Pure function — no
mocks, no I/O.

Selective run: ``pytest tests/test_phishing_tokens.py -q``
"""

import pytest

from app.services.phishing.tokens import generate_tracking_token

URL_SAFE_ALPHABET = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
)


def test_token_is_non_empty_url_safe_string():
    """D1: the token is a non-empty string from the URL-safe alphabet."""
    token = generate_tracking_token()
    assert isinstance(token, str)
    assert len(token) > 0
    assert set(token) <= URL_SAFE_ALPHABET


def test_token_length_matches_token_urlsafe_16():
    """D1: ``token_urlsafe(16)`` yields 22 unpadded base64 chars (128 bits)."""
    token = generate_tracking_token()
    assert len(token) == 22


def test_tokens_are_unique_across_generations():
    """R4/Uniqueness: 100 generations never collide (128-bit entropy)."""
    tokens = {generate_tracking_token() for _ in range(100)}
    assert len(tokens) == 100
