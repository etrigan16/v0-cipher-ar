"""Template CRUD endpoint tests (Phishing Simulator — Phase 2, PR 2).

Covers templates spec R1-R3: tenant-scoped CRUD protected by
``get_current_user``, 404 on cross-tenant / unknown ids, 422 on invalid
payloads, and NULL-tenant seed visibility (design D9).

Selective run: ``pytest tests/test_phishing_templates.py -q``
"""

import pytest

from conftest import Session as AppSession  # same module pytest loaded (shared engine)
from tests.test_asm import _register_and_login


# ── Template CRUD endpoints (spec R1/R2, asm.py conventions) ──────────────


def _template_payload(**overrides) -> dict:
    payload = {
        "name": "Alerta de seguridad",
        "subject": "Aviso para {{nombre}} en {{empresa}}",
        "html_body": '<p>{{nombre}}: <a href="{{link}}">ver</a></p>',
        "category": "bank",
    }
    payload.update(overrides)
    return payload


async def _insert_seed_template(**overrides) -> None:
    """Insert a NULL-tenant seed template into the shared test DB.

    Migration seeds do not run on ``create_all`` (conftest), so the test
    inserts its own seed row to prove seed visibility (spec R3).
    """
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


async def test_templates_require_auth(client):
    """R2: an invalid token is rejected with 401 (repo auth convention).

    A missing Authorization header is caught by HTTPBearer (403); the 401
    path is a malformed-but-present token, which ``get_current_user``
    rejects (same as ``test_auth.py`` invalid-token test).
    """
    resp = await client.get(
        "/phishing/templates", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


async def test_create_template_returns_201_and_appears_in_list(client):
    """R2/Create+list: POST creates a template that the list then shows."""
    headers = await _register_and_login(client, "create@test.com", "Create Corp")
    resp = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Alerta de seguridad"
    assert body["category"] == "bank"
    assert body["id"]

    listing = await client.get("/phishing/templates", headers=headers)
    assert listing.status_code == 200
    names = [t["name"] for t in listing.json()["templates"]]
    assert "Alerta de seguridad" in names


async def test_create_template_invalid_category_422(client):
    """R2/Validation: an invalid category is rejected with 422."""
    headers = await _register_and_login(client, "badcat@test.com", "Bad Cat Corp")
    resp = await client.post(
        "/phishing/templates",
        json=_template_payload(category="sexy"),
        headers=headers,
    )
    assert resp.status_code == 422


async def test_create_template_missing_field_422(client):
    """R2/Validation: a missing required field is rejected with 422."""
    headers = await _register_and_login(client, "nofield@test.com", "No Field Corp")
    payload = _template_payload()
    del payload["html_body"]
    resp = await client.post("/phishing/templates", json=payload, headers=headers)
    assert resp.status_code == 422


async def test_list_includes_seed_templates(client):
    """R3/Seeds: NULL-tenant seed templates appear in every tenant's list."""
    await _insert_seed_template()
    headers = await _register_and_login(client, "seeds@test.com", "Seeds Corp")
    resp = await client.get("/phishing/templates", headers=headers)
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()["templates"]]
    assert "Seed Banco" in names


async def test_list_is_tenant_scoped(client):
    """R1/Isolation: tenant A never sees tenant B's templates."""
    headers_a = await _register_and_login(client, "iso-a@test.com", "Iso A Corp")
    await client.post(
        "/phishing/templates",
        json=_template_payload(name="Solo A"),
        headers=headers_a,
    )
    headers_b = await _register_and_login(client, "iso-b@test.com", "Iso B Corp")
    resp = await client.get("/phishing/templates", headers=headers_b)
    names = [t["name"] for t in resp.json()["templates"]]
    assert "Solo A" not in names


async def test_get_template_detail_returns_own_template(client):
    """R2/Detail: a tenant can fetch its own template by id."""
    headers = await _register_and_login(client, "detail@test.com", "Detail Corp")
    created = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers
    )
    tpl_id = created.json()["id"]

    resp = await client.get(f"/phishing/templates/{tpl_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == tpl_id
    assert body["subject"] == "Aviso para {{nombre}} en {{empresa}}"


async def test_get_template_unknown_id_404(client):
    """R2/Unknown: a nonexistent id returns 404 with no data leak."""
    headers = await _register_and_login(client, "unknown@test.com", "Unknown Corp")
    resp = await client.get(
        "/phishing/templates/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_get_template_cross_tenant_404(client):
    """R2/Cross-tenant: another tenant's template id is a 404, not a leak."""
    headers_a = await _register_and_login(client, "x-a@test.com", "X A Corp")
    created = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers_a
    )
    tpl_id = created.json()["id"]

    headers_b = await _register_and_login(client, "x-b@test.com", "X B Corp")
    resp = await client.get(f"/phishing/templates/{tpl_id}", headers=headers_b)
    assert resp.status_code == 404


async def test_update_own_template_persists_changes(client):
    """R2/Update: PUT changes subject/html_body and the values persist."""
    headers = await _register_and_login(client, "update@test.com", "Update Corp")
    created = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers
    )
    tpl_id = created.json()["id"]

    resp = await client.put(
        f"/phishing/templates/{tpl_id}",
        json=_template_payload(
            subject="Nuevo asunto para {{nombre}}",
            html_body="<p>Nuevo cuerpo {{link}}</p>",
        ),
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject"] == "Nuevo asunto para {{nombre}}"
    assert body["html_body"] == "<p>Nuevo cuerpo {{link}}</p>"

    detail = await client.get(f"/phishing/templates/{tpl_id}", headers=headers)
    assert detail.json()["subject"] == "Nuevo asunto para {{nombre}}"


async def test_update_cross_tenant_404(client):
    """R2/Cross-tenant: PUT on another tenant's template is a 404."""
    headers_a = await _register_and_login(client, "up-a@test.com", "Up A Corp")
    created = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers_a
    )
    tpl_id = created.json()["id"]

    headers_b = await _register_and_login(client, "up-b@test.com", "Up B Corp")
    resp = await client.put(
        f"/phishing/templates/{tpl_id}",
        json=_template_payload(subject="Robado"),
        headers=headers_b,
    )
    assert resp.status_code == 404


async def test_delete_own_template(client):
    """R2/Delete: DELETE removes the template and the list no longer shows it."""
    headers = await _register_and_login(client, "delete@test.com", "Delete Corp")
    created = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers
    )
    tpl_id = created.json()["id"]

    resp = await client.delete(f"/phishing/templates/{tpl_id}", headers=headers)
    assert resp.status_code == 204

    listing = await client.get("/phishing/templates", headers=headers)
    ids = [t["id"] for t in listing.json()["templates"]]
    assert tpl_id not in ids


async def test_delete_cross_tenant_404(client):
    """R2/Cross-tenant: DELETE on another tenant's template is a 404."""
    headers_a = await _register_and_login(client, "del-a@test.com", "Del A Corp")
    created = await client.post(
        "/phishing/templates", json=_template_payload(), headers=headers_a
    )
    tpl_id = created.json()["id"]

    headers_b = await _register_and_login(client, "del-b@test.com", "Del B Corp")
    resp = await client.delete(f"/phishing/templates/{tpl_id}", headers=headers_b)
    assert resp.status_code == 404
