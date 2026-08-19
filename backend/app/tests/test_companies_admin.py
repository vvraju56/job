"""Company endpoints and admin analytics tests."""
from httpx import AsyncClient

from app.models.models import User


async def _make_admin(client: AsyncClient) -> None:
    from app.core.database import SessionLocal
    from app.models.models import User as U

    async with SessionLocal() as db:
        from sqlalchemy import select

        user = (await db.execute(select(U).where(U.email == "tester@example.com"))).scalar_one()
        user.role = "admin"
        await db.commit()


async def test_list_companies(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/companies/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_company_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/companies/does-not-exist")
    assert resp.status_code == 404


async def test_admin_creates_and_gets_analytics(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await _make_admin(client)

    created = await client.post(
        "/api/v1/companies/",
        json={
            "name": "Acme Corp",
            "slug": "acme-corp",
            "website": "https://acme.example",
            "industry": "SaaS",
            "description": "Test company.",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Acme Corp"

    analytics = await client.get("/api/v1/admin/analytics", headers=auth_headers)
    assert analytics.status_code == 200
    data = analytics.json()
    assert data["active_users"] >= 1
    assert isinstance(data["popular_companies"], list)
    assert isinstance(data["jobs_by_source"], list)


async def test_admin_guard(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # tester is admin after _make_admin in the other test; ensure a fresh user is not.
    resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "Not Admin", "email": "notadmin@example.com", "password": "password123"},
    )
    token = resp.json()["access_token"]
    analytics = await client.get(
        "/api/v1/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert analytics.status_code == 403


async def test_broadcast_notification(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await _make_admin(client)
    resp = await client.post(
        "/api/v1/admin/broadcast",
        params={"title": "Welcome", "body": "Hello everyone"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["sent"] >= 1

    notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
    assert any(n["title"] == "Welcome" for n in notifs.json())