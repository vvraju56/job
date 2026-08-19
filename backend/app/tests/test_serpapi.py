"""SerpApi provider, caching, quota, and developer usage tests."""
from datetime import datetime, timezone

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.adapters.base import NormalizedJob
from app.core.database import SessionLocal
from app.models.models import ApiLog


class FakeProvider:
    name = "serpapi"
    configured = True
    supports_query_search = True

    async def search(self, query, location="", page=1, filters=None):
        return [
            NormalizedJob(
                source="serpapi",
                external_id=f"{query.strip()}-{page}-1",
                title=f"{query} Engineer",
                company_name="Serp Co",
                location=location or "Bengaluru, India",
                remote=bool((filters or {}).get("remote")),
                salary_min=1_000_000,
                salary_max=2_000_000,
                salary_currency="INR",
                job_type="full_time",
                level="mid",
                description=f"Role for {query}.",
                apply_url="https://example.com/apply",
                apply_on="Company Website",
                posted_at=datetime.now(timezone.utc),
            )
        ]


class UnconfiguredProvider:
    name = "serpapi"
    configured = False
    supports_query_search = True


@pytest_asyncio.fixture
async def _clean_logs_and_cache():
    from app.services.cache import cache_service

    await cache_service.clear()
    async with SessionLocal() as db:
        await db.execute(delete(ApiLog))
        await db.commit()
    yield


@pytest_asyncio.fixture
async def fake_provider(monkeypatch, _clean_logs_and_cache):
    import app.services.aggregator as agg

    monkeypatch.setattr(agg, "get_enabled_providers", lambda *a, **k: [FakeProvider()])
    yield FakeProvider()


async def test_search_persists_serpapi_jobs(client: AsyncClient, fake_provider) -> None:
    resp = await client.get("/api/v1/jobs/search", params={"query": "Python", "location": "Bengaluru"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["source"] == "serpapi"
    assert item["title"] == "Python Engineer"
    assert item["apply_url"] == "https://example.com/apply"

    # Persisted row is queryable via the relational router.
    detail = await client.get(f"/api/v1/jobs/{item['id']}")
    assert detail.status_code == 200
    assert detail.json()["company_name"] == "Serp Co"


async def test_search_cached_second_request(client: AsyncClient, fake_provider) -> None:
    first = await client.get("/api/v1/jobs/search", params={"query": "Flutter"})
    assert first.status_code == 200
    second = await client.get("/api/v1/jobs/search", params={"query": "Flutter"})
    assert second.status_code == 200
    assert second.json()["items"][0]["id"] == first.json()["items"][0]["id"]

    # Only one non-cached search should be logged; the repeat is a cache hit.
    async with SessionLocal() as db:
        logs = (
            await db.execute(
                select(ApiLog).where(ApiLog.endpoint == "/jobs/search")
            )
        ).scalars().all()
    assert len(logs) == 2
    assert sum(1 for l in logs if not l.cached) == 1
    assert sum(1 for l in logs if l.cached) == 1


async def test_search_filters_remote(client: AsyncClient, fake_provider) -> None:
    resp = await client.get(
        "/api/v1/jobs/search", params={"query": "Go", "remote": "true"}
    )
    assert resp.status_code == 200
    assert resp.json()["items"][0]["remote"] is True


async def test_search_fallback_when_provider_unconfigured(
    client: AsyncClient, monkeypatch, _clean_logs_and_cache
) -> None:
    import app.services.aggregator as agg

    monkeypatch.setattr(agg, "get_enabled_providers", lambda *a, **k: [UnconfiguredProvider()])
    resp = await client.get("/api/v1/jobs/search", params={"query": "Flutter"})
    assert resp.status_code == 200
    # Falls back to relational search (seeded jobs from other tests may exist).
    assert "items" in resp.json()


async def test_quota_exceeded_returns_429(client: AsyncClient, fake_provider, monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "SERPAPI_MONTHLY_LIMIT", 1)
    async with SessionLocal() as db:
        db.add(
            ApiLog(
                endpoint="/jobs/search",
                query="quota",
                cached=False,
                status_code=200,
                created_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()

    resp = await client.get("/api/v1/jobs/search", params={"query": "Quota"})
    assert resp.status_code == 429


async def test_usage_endpoint_admin_only(client: AsyncClient, fake_provider, auth_headers) -> None:
    unauth = await client.get("/api/v1/usage")
    assert unauth.status_code in (401, 403)

    # Fresh non-admin user is rejected.
    plain = await client.post(
        "/api/v1/auth/register",
        json={"name": "Plain User", "email": "plain@example.com", "password": "password123"},
    )
    plain_token = plain.json()["access_token"]
    user_only = await client.get(
        "/api/v1/usage", headers={"Authorization": f"Bearer {plain_token}"}
    )
    assert user_only.status_code == 403

    # Promote the shared tester to admin.
    from sqlalchemy import select

    from app.models.models import User as U

    async with SessionLocal() as db:
        user = (
            await db.execute(select(U).where(U.email == "tester@example.com"))
        ).scalar_one()
        user.role = "admin"
        await db.commit()

    resp = await client.get("/api/v1/usage", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "searches_used" in data
    assert data["monthly_limit"] > 0
    assert data["remaining"] >= 0
    assert isinstance(data["cache"], dict)
    assert isinstance(data["recent_searches"], list)


async def test_cache_stats_and_health(client: AsyncClient, auth_headers) -> None:
    from app.models.models import User as U
    from sqlalchemy import select

    async with SessionLocal() as db:
        user = (
            await db.execute(select(U).where(U.email == "tester@example.com"))
        ).scalar_one()
        user.role = "admin"
        await db.commit()

    stats = await client.get("/api/v1/cache-stats", headers=auth_headers)
    assert stats.status_code == 200
    assert "backend" in stats.json()

    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["provider"] == "serpapi"