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


# ── Public tracking endpoints (spec R1-R6, design D4/D5) ─────────────────────


def _template_payload(**overrides) -> dict:
    payload = {
        "name": "Alerta de seguridad",
        "subject": "Aviso para {{nombre}}",
        "html_body": (
            "<p>Hola {{nombre}} en {{empresa}}:</p>"
            '<p><a href="{{link}}">Verificar</a></p>'
        ),
        "category": "bank",
    }
    payload.update(overrides)
    return payload


async def _launched_campaign(client, headers) -> tuple[str, dict[str, str]]:
    """Template + campaign + 2-target CSV + launch.

    Returns ``(campaign_id, {target_name: tracking_token})``.
    """
    tpl = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers
    )
    assert tpl.status_code == 201
    camp = await client.post(
        "/phishing/campaigns",
        json={"name": "Campaña tracking", "template_id": tpl.json()["id"]},
        headers=headers,
    )
    assert camp.status_code == 201
    cid = camp.json()["id"]

    csv = "email,name\nana@x.com,Ana García\nbob@x.com,Bob Pérez\n"
    up = await client.post(
        f"/phishing/campaigns/{cid}/targets/upload",
        files={"file": ("targets.csv", csv.encode(), "text/csv")},
        headers=headers,
    )
    assert up.status_code == 201

    launch = await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)
    assert launch.status_code == 200
    tokens = {t["name"]: t["tracking_token"] for t in launch.json()["targets"]}
    return cid, tokens


async def _event_rows(token: str) -> list[dict]:
    """All Event rows for a target (oldest first) with parsed metadata."""
    async with AppSession() as s:
        target = (
            await s.execute(select(Target).where(Target.tracking_token == token))
        ).scalar_one_or_none()
        if target is None:
            return []
        rows = (
            await s.execute(
                select(Event)
                .where(Event.target_id == target.id)
                .order_by(Event.occurred_at.asc())
            )
        ).scalars().all()
    return [
        {
            "type": e.type,
            "metadata_": e.metadata_ or "",
            "metadata": json.loads(e.metadata_) if e.metadata_ else {},
        }
        for e in rows
    ]


async def _expire_campaign(campaign_id: str, days_ago: int = 8) -> None:
    """Mark a campaign completed ``days_ago`` days in the past (spec R5)."""
    async with AppSession() as s:
        campaign = await s.get(Campaign, campaign_id)
        campaign.status = "completed"
        campaign.completed_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        await s.commit()


# ── Open pixel (spec R1) ─────────────────────────────────────────────────────


async def test_open_pixel_returns_1x1_png_and_records_open_event(client):
    headers = await _register_and_login(client, "open@test.com", "Open Corp")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]

    resp = await client.get(
        f"/track/open/{token}.png", headers={"User-Agent": "TrackingBot/1.0"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert "no-store" in resp.headers["cache-control"].lower()
    png = resp.content
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG signature
    assert png[16:24] == b"\x00\x00\x00\x01\x00\x00\x00\x01"  # IHDR 1x1

    events = await _event_rows(token)
    assert [e["type"] for e in events] == ["open"]
    assert events[0]["metadata"]["ip"] == "127.0.0.1"
    assert events[0]["metadata"]["user_agent"] == "TrackingBot/1.0"


async def test_open_pixel_unknown_token_404_no_event(client):
    resp = await client.get("/track/open/not-a-real-token.png")
    assert resp.status_code == 404
    assert await _event_rows("not-a-real-token") == []


async def test_open_pixel_expired_token_410_no_event(client):
    headers = await _register_and_login(client, "openexp@test.com", "Open Exp")
    cid, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]
    await _expire_campaign(cid)

    resp = await client.get(f"/track/open/{token}.png")
    assert resp.status_code == 410
    assert await _event_rows(token) == []


# ── Click redirect (spec R2 + design D5 open-redirect guard) ─────────────────


async def test_click_302_to_landing_and_records_click_event(client):
    headers = await _register_and_login(client, "click@test.com", "Click Corp")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Bob Pérez"]

    resp = await client.get(
        f"/track/click/{token}",
        params={"url": "https://bait.example/verify"},
        headers={"User-Agent": "TrackingBot/1.0"},
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == f"/l/{token}"

    events = await _event_rows(token)
    assert [e["type"] for e in events] == ["click"]
    assert events[0]["metadata"]["url"] == "https://bait.example/verify"
    assert events[0]["metadata"]["ip"] == "127.0.0.1"
    assert events[0]["metadata"]["user_agent"] == "TrackingBot/1.0"


async def test_click_never_follows_arbitrary_http_url(client):
    """D5 threat-matrix RED: ?url=https://evil must NOT be the redirect target."""
    headers = await _register_and_login(client, "guard@test.com", "Guard Corp")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]

    resp = await client.get(
        f"/track/click/{token}", params={"url": "https://evil.example/steal?x=1"}
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == f"/l/{token}"  # landing, never evil.example


async def test_click_non_http_url_falls_back_to_landing(client):
    headers = await _register_and_login(client, "guard2@test.com", "Guard 2")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]

    resp = await client.get(
        f"/track/click/{token}", params={"url": "javascript:alert(1)"}
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == f"/l/{token}"


async def test_click_unknown_token_404_no_event(client):
    resp = await client.get(
        "/track/click/not-a-real-token", params={"url": "https://x.example"}
    )
    assert resp.status_code == 404
    assert await _event_rows("not-a-real-token") == []


async def test_click_expired_token_410_no_event(client):
    headers = await _register_and_login(client, "clickexp@test.com", "Click Exp")
    cid, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]
    await _expire_campaign(cid)

    resp = await client.get(
        f"/track/click/{token}", params={"url": "https://x.example"}
    )
    assert resp.status_code == 410
    assert await _event_rows(token) == []


# ── Landing page (spec R3 + design D7 substitution) ──────────────────────────


async def test_landing_renders_substituted_template_and_records_landing_event(client):
    headers = await _register_and_login(client, "land@test.com", "Land Corp")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]

    resp = await client.get(f"/l/{token}", headers={"User-Agent": "TrackingBot/1.0"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    html = resp.text
    assert "Hola Ana García" in html                      # {{nombre}} substituted
    assert f"/track/click/{token}" in html                # {{link}} = tracking click URL
    assert "{{empresa}}" not in html                      # missing key → empty (D7)
    assert "Simulación de phishing" in html               # simulated-capture notice (R3)
    assert 'name="username"' in html and 'name="password"' in html  # credential form

    events = await _event_rows(token)
    assert [e["type"] for e in events] == ["landing"]
    assert events[0]["metadata"]["ip"] == "127.0.0.1"
    assert events[0]["metadata"]["user_agent"] == "TrackingBot/1.0"


async def test_landing_escapes_target_name(client):
    headers = await _register_and_login(client, "escape@test.com", "Escape Corp")
    tpl = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers
    )
    camp = await client.post(
        "/phishing/campaigns",
        json={"name": "Escapa", "template_id": tpl.json()["id"]},
        headers=headers,
    )
    cid = camp.json()["id"]
    csv = "email,name\nx@x.com,<script>alert(1)</script>\n".encode()
    up = await client.post(
        f"/phishing/campaigns/{cid}/targets/upload",
        files={"file": ("t.csv", csv, "text/csv")},
        headers=headers,
    )
    assert up.status_code == 201
    launch = await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)
    token = launch.json()["targets"][0]["tracking_token"]

    html = (await client.get(f"/l/{token}")).text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html  # escaped (D7)
    assert "<script>alert(1)</script>" not in html


async def test_landing_unknown_token_404_no_event(client):
    resp = await client.get("/l/not-a-real-token")
    assert resp.status_code == 404
    assert await _event_rows("not-a-real-token") == []


async def test_landing_expired_token_410_no_event(client):
    headers = await _register_and_login(client, "landexp@test.com", "Land Exp")
    cid, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]
    await _expire_campaign(cid)

    resp = await client.get(f"/l/{token}")
    assert resp.status_code == 410
    assert await _event_rows(token) == []


# ── Simulated credential capture (spec R4 + design D4 hashing) ───────────────


async def test_credential_submit_records_sha256_hash_only(client):
    headers = await _register_and_login(client, "cred@test.com", "Cred Corp")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]

    resp = await client.post(
        f"/l/{token}/submit",
        data={"username": "ana.garcia", "password": "sup3rsecret"},
        headers={"User-Agent": "TrackingBot/1.0"},
    )
    assert resp.status_code == 200
    assert "Simulación" in resp.text

    events = await _event_rows(token)
    assert [e["type"] for e in events] == ["credential"]
    meta = events[0]["metadata"]
    assert meta["hash"] == hashlib.sha256(b"ana.garcia:sup3rsecret").hexdigest()
    assert meta["username_sha256"] == hashlib.sha256(b"ana.garcia").hexdigest()
    assert meta["password_sha256"] == hashlib.sha256(b"sup3rsecret").hexdigest()
    assert meta["ip"] == "127.0.0.1"


async def test_credential_plaintext_never_stored(client):
    headers = await _register_and_login(client, "nopw@test.com", "No Pw")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]

    resp = await client.post(
        f"/l/{token}/submit",
        data={"username": "ana.garcia", "password": "sup3rsecret"},
    )
    assert resp.status_code == 200

    rows = await _event_rows(token)
    assert [r["type"] for r in rows] == ["credential"]
    raw = rows[0]["metadata_"]
    assert "sup3rsecret" not in raw  # password plaintext never persisted (R4/D4)
    assert "ana.garcia" not in raw   # username also only stored hashed


async def test_credential_submit_unknown_token_404_no_event(client):
    resp = await client.post(
        "/l/not-a-real-token/submit",
        data={"username": "u", "password": "p"},
    )
    assert resp.status_code == 404
    assert await _event_rows("not-a-real-token") == []


async def test_credential_submit_expired_token_410_no_event(client):
    headers = await _register_and_login(client, "credexp@test.com", "Cred Exp")
    cid, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]
    await _expire_campaign(cid)

    resp = await client.post(
        f"/l/{token}/submit", data={"username": "u", "password": "p"}
    )
    assert resp.status_code == 410
    assert await _event_rows(token) == []


# ── Report (spec R6) ─────────────────────────────────────────────────────────


async def test_report_records_event(client):
    headers = await _register_and_login(client, "rep@test.com", "Rep Corp")
    _, tokens = await _launched_campaign(client, headers)
    token = tokens["Bob Pérez"]

    resp = await client.post(
        f"/l/{token}/report", headers={"User-Agent": "TrackingBot/1.0"}
    )
    assert resp.status_code == 200
    assert "Gracias" in resp.text

    events = await _event_rows(token)
    assert [e["type"] for e in events] == ["report"]
    assert events[0]["metadata"]["ip"] == "127.0.0.1"
    assert events[0]["metadata"]["user_agent"] == "TrackingBot/1.0"


async def test_report_unknown_token_404_no_event(client):
    resp = await client.post("/l/not-a-real-token/report")
    assert resp.status_code == 404
    assert await _event_rows("not-a-real-token") == []


async def test_report_expired_token_410_no_event(client):
    headers = await _register_and_login(client, "repexp@test.com", "Rep Exp")
    cid, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]
    await _expire_campaign(cid)

    resp = await client.post(f"/l/{token}/report")
    assert resp.status_code == 410
    assert await _event_rows(token) == []


# ── 7-day expiry window (spec R5) ────────────────────────────────────────────


async def test_completed_6_days_ago_still_resolves_all_endpoints(client):
    """Tokens stay valid for 7 days past ``completed_at`` (spec R5)."""
    headers = await _register_and_login(client, "win@test.com", "Win Corp")
    cid, tokens = await _launched_campaign(client, headers)
    token = tokens["Ana García"]
    await _expire_campaign(cid, days_ago=6)

    assert (await client.get(f"/track/open/{token}.png")).status_code == 200
    assert (await client.get(f"/track/click/{token}")).status_code == 302
    assert (await client.get(f"/l/{token}")).status_code == 200
