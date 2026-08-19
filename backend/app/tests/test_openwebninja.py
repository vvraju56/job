"""OpenWebNinja salary/autocomplete and keyless /jobs/public endpoint tests."""
from datetime import datetime, timezone

import pytest_asyncio
from httpx import AsyncClient

from app.adapters.base import NormalizedJob
from app.services.providers.base import ProviderNotConfigured


class FakeAddon:
    async def job_salary(self, job_title, location=""):
        return {"data": [{"job_title": job_title, "salary": 120000}]}, False

    async def autocomplete(self, query):
        return {"suggestions": [query + " engineer", query + " developer"]}, False


@pytest_asyncio.fixture
async def fake_addon(monkeypatch):
    import app.services.openwebninja as ow

    monkeypatch.setattr(ow, "job_salary", FakeAddon().job_salary)
    monkeypatch.setattr(ow, "autocomplete", FakeAddon().autocomplete)
    yield ow


class FakeBoardProvider:
    def __init__(self, name):
        self.name = name

    async def search(self, query, location="", page=1, filters=None):
        return [
            NormalizedJob(
                source=self.name,
                external_id=f"{self.name}-1",
                title=f"{self.name.title()} Engineer",
                company_name=f"{self.name.title()} Inc",
                location="Remote",
                remote=True,
                description=f"{self.name.title()} posting.",
                apply_url=f"https://{self.name}.example.com/jobs/1",
                apply_on=self.name.title(),
                posted_at=datetime.now(timezone.utc),
            )
        ]


async def test_salary_endpoint(client: AsyncClient, fake_addon) -> None:
    resp = await client.get("/api/v1/jobs/salary", params={"job_title": "Node.js", "location": "New York"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "openwebninja"
    assert body["cached"] is False
    assert body["data"]["data"][0]["job_title"] == "Node.js"


async def test_autocomplete_endpoint(client: AsyncClient, fake_addon) -> None:
    resp = await client.get("/api/v1/jobs/autocomplete", params={"query": "python"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "openwebninja"
    assert "python engineer" in body["data"]["suggestions"]


async def test_salary_endpoint_503_when_unconfigured(client: AsyncClient, monkeypatch) -> None:
    import app.services.openwebninja as ow

    async def _boom(job_title, location=""):
        raise ProviderNotConfigured("JSEARCH_API_KEY is not configured.")

    monkeypatch.setattr(ow, "job_salary", _boom)
    resp = await client.get("/api/v1/jobs/salary", params={"job_title": "Go"})
    assert resp.status_code == 503


async def test_public_endpoint_returns_keyless_feeds(client: AsyncClient, monkeypatch) -> None:
    import app.api.routes.serpapi as routes

    providers = {name: FakeBoardProvider(name) for name in ("greenhouse", "ashby", "remoteok")}
    monkeypatch.setattr(routes, "get_provider", lambda name: providers[name])

    resp = await client.get("/api/v1/jobs/public")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"greenhouse", "ashby", "remoteok"}
    for name, items in body.items():
        assert len(items) == 1
        assert items[0]["source"] == name
        assert items[0]["apply_url"].startswith(f"https://{name}.example.com/")


async def test_public_endpoint_isolates_failures(client: AsyncClient, monkeypatch) -> None:
    import app.api.routes.serpapi as routes

    async def _boom(query, location="", page=1, filters=None):
        raise RuntimeError("board down")

    providers = {
        "greenhouse": FakeBoardProvider("greenhouse"),
        "ashby": FakeBoardProvider("ashby"),
        "remoteok": type("Broken", (), {"name": "remoteok", "search": _boom})(),
    }
    monkeypatch.setattr(routes, "get_provider", lambda name: providers[name])

    resp = await client.get("/api/v1/jobs/public")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["greenhouse"]) == 1
    assert len(body["ashby"]) == 1
    assert body["remoteok"] == []