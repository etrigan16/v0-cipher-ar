"""Campaign CRUD + CSV upload + launch/cancel endpoint tests (Phase 3, PR 3).

Covers campaigns spec R1-R6: tenant-scoped campaign CRUD, CSV target upload
(valid/invalid/dedupe — 422 with zero persisted, design D6), launch (unique
tokens, draft-only, needs targets) and cancel (draft|active). Reuses the
asm.py ``_register_and_login`` helper and the conftest in-memory SQLite.

Selective run: ``pytest tests/test_phishing_campaigns.py -q``
"""

from conftest import Session as AppSession  # same module pytest loaded (shared engine)
from tests.test_asm import _register_and_login

from app.models.campaign import Campaign


def _template_payload(**overrides) -> dict:
    payload = {
        "name": "Alerta de seguridad",
        "subject": "Aviso para {{nombre}} en {{empresa}}",
        "html_body": '<p>{{nombre}}: <a href="{{link}}">ver</a></p>',
        "category": "bank",
    }
    payload.update(overrides)
    return payload


async def _create_template(client, headers, **overrides) -> str:
    resp = await client.post(
        "/phishing/templates", json=_template_payload(**overrides), headers=headers
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _insert_seed_template(**overrides) -> None:
    """Insert a NULL-tenant seed template (migration seeds do not run on create_all)."""
    from app.models.template import Template

    fields = {
        "name": "Seed Banco",
        "subject": "Seed {{nombre}} en {{empresa}}",
        "html_body": "<p>{{nombre}} {{link}}</p>",
        "category": "bank",
    }
    fields.update(overrides)
    async with AppSession() as s:
        s.add(Template(tenant_id=None, **fields))
        await s.commit()


async def _create_campaign(client, headers, template_id, **overrides) -> str:
    payload = {"name": "Campaña de prueba", "template_id": template_id}
    payload.update(overrides)
    resp = await client.post("/phishing/campaigns", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def _csv_bytes(*rows: str, header: bool = True) -> bytes:
    lines = list(rows)
    if header:
        lines.insert(0, "email,name")
    return "\n".join(lines).encode()


async def _upload_csv(client, headers, campaign_id, content: bytes) -> object:
    return await client.post(
        f"/phishing/campaigns/{campaign_id}/targets/upload",
        files={"file": ("targets.csv", content, "text/csv")},
        headers=headers,
    )


async def _set_campaign_status(campaign_id: str, status: str) -> None:
    async with AppSession() as s:
        campaign = await s.get(Campaign, campaign_id)
        campaign.status = status
        await s.commit()


# ── Create (spec R1, launch prompt: template ownership validation) ──────────


async def test_campaigns_require_auth(client):
    resp = await client.get(
        "/phishing/campaigns", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


async def test_create_campaign_returns_201_and_draft(client):
    headers = await _register_and_login(client, "camp@test.com", "Camp Corp")
    tpl = await _create_template(client, headers)

    resp = await client.post(
        "/phishing/campaigns",
        json={"name": "Campaña de prueba", "template_id": tpl},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Campaña de prueba"
    assert body["template_id"] == tpl
    assert body["status"] == "draft"
    assert body["started_at"] is None


async def test_create_campaign_with_seed_template(client):
    """D9: NULL-tenant seed templates are usable by every tenant."""
    await _insert_seed_template(name="Seed Banco")
    headers = await _register_and_login(client, "seedcamp@test.com", "Seed Camp")
    listing = await client.get("/phishing/templates", headers=headers)
    seed_id = next(
        t["id"] for t in listing.json()["templates"] if t["name"] == "Seed Banco"
    )

    resp = await client.post(
        "/phishing/campaigns",
        json={"name": "Con semilla", "template_id": seed_id},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["template_id"] == seed_id


async def test_create_campaign_unknown_template_404(client):
    headers = await _register_and_login(client, "badtpl@test.com", "Bad Tpl")
    resp = await client.post(
        "/phishing/campaigns",
        json={
            "name": "Sin plantilla",
            "template_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=headers,
    )
    assert resp.status_code == 404


async def test_create_campaign_cross_tenant_template_404(client):
    """R6: a template owned by another tenant is not usable (no leak)."""
    headers_a = await _register_and_login(client, "ct-a@test.com", "CT A Corp")
    tpl_a = await _create_template(client, headers_a)

    headers_b = await _register_and_login(client, "ct-b@test.com", "CT B Corp")
    resp = await client.post(
        "/phishing/campaigns",
        json={"name": "Ajena", "template_id": tpl_a},
        headers=headers_b,
    )
    assert resp.status_code == 404


async def test_create_campaign_missing_name_422(client):
    headers = await _register_and_login(client, "noname@test.com", "No Name")
    tpl = await _create_template(client, headers)
    resp = await client.post(
        "/phishing/campaigns", json={"template_id": tpl}, headers=headers
    )
    assert resp.status_code == 422


# ── List / detail (spec R2/R6) ───────────────────────────────────────────────


async def test_list_campaigns_is_tenant_scoped(client):
    headers_a = await _register_and_login(client, "li-a@test.com", "Li A Corp")
    tpl_a = await _create_template(client, headers_a)
    await _create_campaign(client, headers_a, tpl_a)

    headers_b = await _register_and_login(client, "li-b@test.com", "Li B Corp")
    resp = await client.get("/phishing/campaigns", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json()["campaigns"] == []


async def test_list_campaigns_includes_target_counts(client):
    headers = await _register_and_login(client, "count@test.com", "Count Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    await _upload_csv(
        client,
        headers,
        cid,
        _csv_bytes("ana@x.com,Ana", "bob@x.com,Bob"),
    )

    resp = await client.get("/phishing/campaigns", headers=headers)
    campaigns = resp.json()["campaigns"]
    mine = next(c for c in campaigns if c["id"] == cid)
    assert mine["target_count"] == 2


async def test_get_campaign_detail(client):
    headers = await _register_and_login(client, "det@test.com", "Det Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await client.get(f"/phishing/campaigns/{cid}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == cid
    assert body["name"] == "Campaña de prueba"
    assert body["status"] == "draft"
    assert body["target_count"] == 0


async def test_get_campaign_unknown_404(client):
    headers = await _register_and_login(client, "unk@test.com", "Unk Corp")
    resp = await client.get(
        "/phishing/campaigns/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 404


async def test_get_campaign_cross_tenant_404(client):
    headers_a = await _register_and_login(client, "gd-a@test.com", "Gd A Corp")
    tpl_a = await _create_template(client, headers_a)
    cid = await _create_campaign(client, headers_a, tpl_a)

    headers_b = await _register_and_login(client, "gd-b@test.com", "Gd B Corp")
    resp = await client.get(f"/phishing/campaigns/{cid}", headers=headers_b)
    assert resp.status_code == 404


# ── Update (launch prompt: draft-only, else 409; R1 invalid status) ──────────


async def test_update_draft_campaign_persists(client):
    headers = await _register_and_login(client, "upd@test.com", "Upd Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await client.put(
        f"/phishing/campaigns/{cid}",
        json={"name": "Renombrada", "template_id": tpl},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renombrada"

    detail = await client.get(f"/phishing/campaigns/{cid}", headers=headers)
    assert detail.json()["name"] == "Renombrada"


async def test_update_non_draft_409(client):
    headers = await _register_and_login(client, "updnd@test.com", "Upd ND")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    await _upload_csv(client, headers, cid, _csv_bytes("ana@x.com,Ana"))
    await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)

    resp = await client.put(
        f"/phishing/campaigns/{cid}",
        json={"name": "No editable", "template_id": tpl},
        headers=headers,
    )
    assert resp.status_code == 409


async def test_update_invalid_status_422_status_unchanged(client):
    """R1: an out-of-domain status in the body is 422 and never applied."""
    headers = await _register_and_login(client, "st@test.com", "St Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await client.put(
        f"/phishing/campaigns/{cid}",
        json={"name": "X", "template_id": tpl, "status": "exploded"},
        headers=headers,
    )
    assert resp.status_code == 422

    detail = await client.get(f"/phishing/campaigns/{cid}", headers=headers)
    assert detail.json()["status"] == "draft"


async def test_update_cross_tenant_404(client):
    headers_a = await _register_and_login(client, "uu-a@test.com", "Uu A Corp")
    tpl_a = await _create_template(client, headers_a)
    cid = await _create_campaign(client, headers_a, tpl_a)

    headers_b = await _register_and_login(client, "uu-b@test.com", "Uu B Corp")
    resp = await client.put(
        f"/phishing/campaigns/{cid}",
        json={"name": "Robado", "template_id": tpl_a},
        headers=headers_b,
    )
    assert resp.status_code == 404


# ── Delete (launch prompt: draft-only, else 409) ─────────────────────────────


async def test_delete_draft_campaign(client):
    headers = await _register_and_login(client, "del@test.com", "Del Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await client.delete(f"/phishing/campaigns/{cid}", headers=headers)
    assert resp.status_code == 204

    listing = await client.get("/phishing/campaigns", headers=headers)
    assert [c["id"] for c in listing.json()["campaigns"]] == []


async def test_delete_non_draft_409(client):
    headers = await _register_and_login(client, "delnd@test.com", "Del ND")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    await _upload_csv(client, headers, cid, _csv_bytes("ana@x.com,Ana"))
    await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)

    resp = await client.delete(f"/phishing/campaigns/{cid}", headers=headers)
    assert resp.status_code == 409


async def test_delete_cross_tenant_404(client):
    headers_a = await _register_and_login(client, "dd-a@test.com", "Dd A Corp")
    tpl_a = await _create_template(client, headers_a)
    cid = await _create_campaign(client, headers_a, tpl_a)

    headers_b = await _register_and_login(client, "dd-b@test.com", "Dd B Corp")
    resp = await client.delete(f"/phishing/campaigns/{cid}", headers=headers_b)
    assert resp.status_code == 404


# ── CSV upload (spec R2/R3, design D6 — validate first, 422, zero persisted) ─


async def test_upload_valid_csv_creates_pending_targets(client):
    headers = await _register_and_login(client, "up@test.com", "Up Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await _upload_csv(
        client,
        headers,
        cid,
        _csv_bytes("ana@x.com,Ana García", "bob@x.com,Bob Pérez"),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["count"] == 2
    emails = {t["email"] for t in body["targets"]}
    assert emails == {"ana@x.com", "bob@x.com"}
    for t in body["targets"]:
        assert t["status"] == "pending"
        assert t["tracking_token"] is None

    listing = await client.get(f"/phishing/campaigns/{cid}/targets", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()["targets"]) == 2


async def test_upload_requires_auth(client):
    resp = await _upload_csv(
        client,
        {"Authorization": "Bearer not-a-real-token"},
        "00000000-0000-0000-0000-000000000000",
        _csv_bytes("ana@x.com,Ana"),
    )
    assert resp.status_code == 401


async def test_upload_cross_tenant_campaign_404(client):
    headers_a = await _register_and_login(client, "cp-a@test.com", "Cp A Corp")
    tpl_a = await _create_template(client, headers_a)
    cid = await _create_campaign(client, headers_a, tpl_a)

    headers_b = await _register_and_login(client, "cp-b@test.com", "Cp B Corp")
    resp = await _upload_csv(client, headers_b, cid, _csv_bytes("ana@x.com,Ana"))
    assert resp.status_code == 404


async def test_upload_invalid_email_422_zero_persisted(client):
    headers = await _register_and_login(client, "badem@test.com", "Bad Em")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await _upload_csv(
        client, headers, cid, _csv_bytes("ana@x.com,Ana", "not-an-email,Bob")
    )
    assert resp.status_code == 422

    listing = await client.get(f"/phishing/campaigns/{cid}/targets", headers=headers)
    assert listing.json()["targets"] == []


async def test_upload_missing_email_422(client):
    headers = await _register_and_login(client, "noem@test.com", "No Em")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await _upload_csv(client, headers, cid, _csv_bytes("solo-nombre"))
    assert resp.status_code == 422


async def test_upload_duplicate_within_file_422(client):
    headers = await _register_and_login(client, "dupe@test.com", "Dupe Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await _upload_csv(
        client, headers, cid, _csv_bytes("ana@x.com,Ana", "ana@x.com,Ana Dos")
    )
    assert resp.status_code == 422

    listing = await client.get(f"/phishing/campaigns/{cid}/targets", headers=headers)
    assert listing.json()["targets"] == []


async def test_upload_duplicate_against_existing_target_422(client):
    headers = await _register_and_login(client, "dupe2@test.com", "Dupe 2")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    first = await _upload_csv(client, headers, cid, _csv_bytes("ana@x.com,Ana"))
    assert first.status_code == 201

    resp = await _upload_csv(client, headers, cid, _csv_bytes("ana@x.com,Otra"))
    assert resp.status_code == 422

    listing = await client.get(f"/phishing/campaigns/{cid}/targets", headers=headers)
    assert len(listing.json()["targets"]) == 1


async def test_upload_empty_csv_422(client):
    headers = await _register_and_login(client, "empty@test.com", "Empty Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await _upload_csv(client, headers, cid, b"email,name\n")
    assert resp.status_code == 422


# ── Launch (spec R4 — unique tokens, draft-only, needs targets) ──────────────


async def test_launch_generates_unique_tokens_and_activates(client):
    headers = await _register_and_login(client, "launch@test.com", "Launch Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    await _upload_csv(
        client,
        headers,
        cid,
        _csv_bytes("ana@x.com,Ana", "bob@x.com,Bob", "carl@x.com,Carl"),
    )

    resp = await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["campaign"]["status"] == "active"
    assert body["campaign"]["started_at"] is not None
    tokens = [t["tracking_token"] for t in body["targets"]]
    assert len(tokens) == 3
    assert len(set(tokens)) == 3  # R4 token uniqueness
    for t in body["targets"]:
        assert t["landing_url"].endswith(f"/l/{t['tracking_token']}")
        assert t["status"] == "active"

    detail = await client.get(f"/phishing/campaigns/{cid}", headers=headers)
    assert detail.json()["status"] == "active"


async def test_launch_no_targets_409(client):
    headers = await _register_and_login(client, "noreg@test.com", "No Reg")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)
    assert resp.status_code == 409


async def test_launch_non_draft_409_tokens_unchanged(client):
    headers = await _register_and_login(client, "twice@test.com", "Twice Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    await _upload_csv(client, headers, cid, _csv_bytes("ana@x.com,Ana"))

    first = await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)
    assert first.status_code == 200
    original_tokens = [t["tracking_token"] for t in first.json()["targets"]]

    resp = await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)
    assert resp.status_code == 409

    listing = await client.get(f"/phishing/campaigns/{cid}/targets", headers=headers)
    current_tokens = [t["tracking_token"] for t in listing.json()["targets"]]
    assert current_tokens == original_tokens


async def test_launch_cross_tenant_404(client):
    headers_a = await _register_and_login(client, "ln-a@test.com", "Ln A Corp")
    tpl_a = await _create_template(client, headers_a)
    cid = await _create_campaign(client, headers_a, tpl_a)

    headers_b = await _register_and_login(client, "ln-b@test.com", "Ln B Corp")
    resp = await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers_b)
    assert resp.status_code == 404


# ── Cancel (spec R5 — draft|active → cancelled + completed_at) ───────────────


async def test_cancel_active_campaign(client):
    headers = await _register_and_login(client, "can@test.com", "Can Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    await _upload_csv(client, headers, cid, _csv_bytes("ana@x.com,Ana"))
    await client.post(f"/phishing/campaigns/{cid}/launch", headers=headers)

    resp = await client.post(f"/phishing/campaigns/{cid}/cancel", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "cancelled"
    assert body["completed_at"] is not None


async def test_cancel_draft_campaign(client):
    """R5: draft campaigns may also be cancelled."""
    headers = await _register_and_login(client, "cand@test.com", "Can Draft")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)

    resp = await client.post(f"/phishing/campaigns/{cid}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


async def test_cancel_completed_campaign_409(client):
    headers = await _register_and_login(client, "done@test.com", "Done Corp")
    tpl = await _create_template(client, headers)
    cid = await _create_campaign(client, headers, tpl)
    await _set_campaign_status(cid, "completed")

    resp = await client.post(f"/phishing/campaigns/{cid}/cancel", headers=headers)
    assert resp.status_code == 409


async def test_cancel_cross_tenant_404(client):
    headers_a = await _register_and_login(client, "cn-a@test.com", "Cn A Corp")
    tpl_a = await _create_template(client, headers_a)
    cid = await _create_campaign(client, headers_a, tpl_a)

    headers_b = await _register_and_login(client, "cn-b@test.com", "Cn B Corp")
    resp = await client.post(f"/phishing/campaigns/{cid}/cancel", headers=headers_b)
    assert resp.status_code == 404
