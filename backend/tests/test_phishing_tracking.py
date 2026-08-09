"""Tracking/landing service + public endpoint tests (Phase 4, PR 4).

Covers the tracking spec R1-R6 and design D2-D5: the campaign-state token
expiry rule (D2), the event recording helper (D3), and the public token-gated
endpoints — open pixel (R1), click redirect (R2), landing page (R3),
simulated credential capture with one-way SHA-256 hashing (D4) and report
(R6). Unknown tokens → 404 and expired campaigns → 410, and neither records
an Event (spec R1/R2/R5).

Selective run: ``pytest tests/test_phishing_tracking.py -q``
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from conftest import Session as AppSession
from tests.test_asm import _register_and_login

from app.models.campaign import Campaign
from app.models.event import Event
from app.models.target import Target
from app.services.phishing.landing import is_tracking_expired

# ── Expiry rule (design D2 / spec R5) ────────────────────────────────────────


def test_expiry_active_campaign_never_expires():
    campaign = Campaign(status="active")
    assert is_tracking_expired(campaign) is False


def test_expiry_completed_within_7_day_window_is_valid():
    campaign = Campaign(
        status="completed",
        completed_at=datetime.now(timezone.utc) - timedelta(days=6),
    )
    assert is_tracking_expired(campaign) is False


def test_expiry_completed_8_days_ago_is_expired():
    campaign = Campaign(
        status="completed",
        completed_at=datetime.now(timezone.utc) - timedelta(days=8),
    )
    assert is_tracking_expired(campaign) is True


def test_expiry_cancelled_campaign_is_expired():
    assert is_tracking_expired(Campaign(status="cancelled")) is True


def test_expiry_draft_campaign_is_expired():
    assert is_tracking_expired(Campaign(status="draft")) is True


def test_expiry_handles_naive_sqlite_datetimes():
    naive = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=8)
    assert is_tracking_expired(Campaign(status="completed", completed_at=naive)) is True
