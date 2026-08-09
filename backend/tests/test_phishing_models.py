"""Model persistence tests for the phishing models.

Phase 1 (PR 1): Template/Campaign/Target/Event models with tenant FKs, unique
constraints, and server defaults (``created_at``, ``status``).
"""

import json

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.campaign import Campaign
from app.models.event import Event
from app.models.target import Target
from app.models.template import Template
from app.models.tenant import Tenant


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite session with the full (registered) metadata."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, expire_on_commit=False)
    async with session() as s:
        yield s
    await engine.dispose()


async def _make_tenant(db_session, slug: str = "acme") -> Tenant:
    tenant = Tenant(name="Acme", slug=slug)
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _make_template(db_session, tenant_id) -> Template:
    tpl = Template(
        tenant_id=tenant_id,
        name="Alerta",
        subject="Hola {{nombre}} en {{empresa}}",
        html_body='<p>{{nombre}}, {{empresa}}: <a href="{{link}}">ver</a></p>',
        category="bank",
    )
    db_session.add(tpl)
    await db_session.flush()
    return tpl


async def _make_campaign(db_session, tenant_id, template_id) -> Campaign:
    camp = Campaign(name="Campaña 1", tenant_id=tenant_id, template_id=template_id)
    db_session.add(camp)
    await db_session.flush()
    return camp


# ── Template ──────────────────────────────────────────────────────────────


async def test_template_persists_with_tenant_and_defaults(db_session):
    tenant = await _make_tenant(db_session)
    tpl = Template(
        tenant_id=tenant.id,
        name="Alerta de seguridad",
        subject="Aviso para {{nombre}}",
        html_body="<p>{{nombre}} {{empresa}} {{link}}</p>",
        category="bank",
    )
    db_session.add(tpl)
    await db_session.commit()
    await db_session.refresh(tpl)

    assert tpl.id is not None
    assert tpl.tenant_id == tenant.id
    assert tpl.category == "bank"
    assert tpl.subject == "Aviso para {{nombre}}"
    assert tpl.created_at is not None  # server_default=func.now()


async def test_seed_template_persists_with_null_tenant(db_session):
    """D9: seed templates carry tenant_id NULL — visible to every tenant."""
    tpl = Template(name="Seed", subject="S", html_body="B", category="tech")
    db_session.add(tpl)
    await db_session.commit()
    await db_session.refresh(tpl)
    assert tpl.tenant_id is None
    assert tpl.id is not None


# ── Campaign ──────────────────────────────────────────────────────────────


async def test_campaign_persists_draft_with_nullable_dates(db_session):
    tenant = await _make_tenant(db_session)
    tpl = await _make_template(db_session, tenant.id)
    camp = Campaign(name="Campaña Q3", tenant_id=tenant.id, template_id=tpl.id)
    db_session.add(camp)
    await db_session.commit()
    await db_session.refresh(camp)

    assert camp.status == "draft"  # server default
    assert camp.started_at is None
    assert camp.completed_at is None
    assert camp.created_at is not None
    assert camp.template_id == tpl.id


# ── Target ────────────────────────────────────────────────────────────────


async def test_target_defaults_pending_and_token_null(db_session):
    tenant = await _make_tenant(db_session)
    tpl = await _make_template(db_session, tenant.id)
    camp = await _make_campaign(db_session, tenant.id, tpl.id)
    target = Target(tenant_id=tenant.id, campaign_id=camp.id, email="a@x.com", name="A")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    assert target.status == "pending"  # server default
    assert target.tracking_token is None  # token assigned at launch (R4)


async def test_target_duplicate_email_in_campaign_rejected(db_session):
    tenant = await _make_tenant(db_session)
    tpl = await _make_template(db_session, tenant.id)
    camp = await _make_campaign(db_session, tenant.id, tpl.id)
    db_session.add_all(
        [
            Target(tenant_id=tenant.id, campaign_id=camp.id, email="a@x.com", name="A"),
            Target(tenant_id=tenant.id, campaign_id=camp.id, email="a@x.com", name="B"),
        ]
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_tracking_token_unique_across_campaigns(db_session):
    tenant = await _make_tenant(db_session)
    tpl = await _make_template(db_session, tenant.id)
    camp_a = await _make_campaign(db_session, tenant.id, tpl.id)
    camp_b = await _make_campaign(db_session, tenant.id, tpl.id)
    db_session.add_all(
        [
            Target(
                tenant_id=tenant.id, campaign_id=camp_a.id,
                email="a@x.com", name="A", tracking_token="tok-1",
            ),
            Target(
                tenant_id=tenant.id, campaign_id=camp_b.id,
                email="b@x.com", name="B", tracking_token="tok-1",
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


# ── Event ─────────────────────────────────────────────────────────────────


async def test_event_persists_with_metadata_json_and_occurred_at(db_session):
    tenant = await _make_tenant(db_session)
    tpl = await _make_template(db_session, tenant.id)
    camp = await _make_campaign(db_session, tenant.id, tpl.id)
    target = Target(tenant_id=tenant.id, campaign_id=camp.id, email="a@x.com", name="A")
    db_session.add(target)
    await db_session.flush()

    ev = Event(
        tenant_id=tenant.id,
        campaign_id=camp.id,
        target_id=target.id,
        type="click",
        metadata_=json.dumps(
            {"ip": "203.0.113.7", "user_agent": "curl/8", "url": "https://x.test"}
        ),
    )
    db_session.add(ev)
    await db_session.commit()
    await db_session.refresh(ev)

    assert ev.type == "click"
    assert ev.campaign_id == camp.id
    assert ev.target_id == target.id
    assert ev.occurred_at is not None
    assert json.loads(ev.metadata_)["user_agent"] == "curl/8"
