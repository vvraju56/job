"""Multi-source aggregation: fan-out, cross-provider dedupe, normalization."""
from datetime import datetime, timezone

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.adapters.base import NormalizedJob
from app.core.database import SessionLocal
from app.models.models import ApiLog, Job
from app.services.aggregator import dedupe_jobs


def _job(source: str, external_id: str, title: str, company: str = "Acme", apply_url: str = "https://acme.com/jobs/1") -> NormalizedJob:
    return NormalizedJob(
        source=source,
        external_id=external_id,
        title=title,
        company_name=company,
        location="Chennai, India",
        apply_url=apply_url,
        job_type="full_time",
        level="mid",
        posted_at=datetime.now(timezone.utc),
    )


class FakeSerp:
    name = "serpapi"
    configured = True
    supports_query_search = True

    async def search(self, query, location="", page=1, filters=None):
        return [_job("serpapi", "s1", f"{query} Engineer")]


class FakeJSearch:
    name = "jsearch"
    configured = True
    supports_query_search = True

    async def search(self, query, location="", page=1, filters=None):
        # Same posting as serpapi → must be dropped. Distinct posting → kept.
        return [
            _job("jsearch", "j1", f"{query} Engineer", apply_url="https://acme.com/jobs/1"),
            _job("jsearch", "j2", f"{query} Designer", apply_url="https://acme.com/jobs/2"),
        ]


@pytest_asyncio.fixture
async def _cleanup():
    from app.services.cache import cache_service

    await cache_service.clear()
    async with SessionLocal() as db:
        await db.execute(delete(ApiLog))
        await db.commit()
    yield


def test_dedupe_keeps_higher_priority() -> None:
    jobs = [
        _job("remoteok", "r1", "Flutter Developer"),
        _job("usajobs", "u1", "Flutter Developer"),
        _job("serpapi", "s1", "Flutter Developer"),
    ]
    result = dedupe_jobs(jobs, ["serpapi", "jsearch", "greenhouse", "ashby", "usajobs", "remoteok"])
    assert len(result) == 1
    assert result[0].source == "serpapi"


def test_dedupe_distinct_postings_kept() -> None:
    jobs = [
        _job("serpapi", "s1", "Flutter Developer"),
        _job("jsearch", "j1", "Flutter Developer", apply_url="https://acme.com/jobs/2"),
    ]
    result = dedupe_jobs(jobs, ["serpapi", "jsearch", "greenhouse", "ashby", "usajobs", "remoteok"])
    assert len(result) == 2


async def test_aggregate_fans_out_and_dedupes(
    client: AsyncClient, monkeypatch, _cleanup
) -> None:
    import app.services.aggregator as agg

    monkeypatch.setattr(agg, "get_enabled_providers", lambda *a, **k: [FakeSerp(), FakeJSearch()])

    resp = await client.get("/api/v1/jobs/search", params={"query": "Flutter"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    # serpapi "Flutter Engineer" wins; jsearch "Flutter Designer" kept → 2 jobs.
    assert len(items) == 2
    sources = {item["source"] for item in items}
    assert sources == {"serpapi", "jsearch"}
    assert any(item["title"] == "Flutter Engineer" for item in items)

    async with SessionLocal() as db:
        jobs = (await db.execute(select(Job))).scalars().all()
    assert any(j.source == "serpapi" and j.external_id == "s1" for j in jobs)
    assert any(j.source == "jsearch" and j.external_id == "j2" for j in jobs)


def test_usajobs_normalize() -> None:
    from app.services.providers.usajobs import usajobs_provider

    raw = {
        "MatchedObjectDescriptor": {
            "PositionID": "ABC123",
            "PositionTitle": "Software Engineer",
            "OrganizationName": "US Navy",
            "PositionLocation": [{"LocationName": "Washington, DC"}],
            "IsRemote": True,
            "PositionSalary": [{"MinimumRange": 90000, "MaximumRange": 120000}],
            "PositionSchedule": [{"Schedule": "Full-time"}],
            "JobSummary": "Build critical systems.",
            "ApplyURI": "https://www.usajobs.gov/GetJob/ViewDetails/ABC123",
            "PublicationStartDate": "2026-08-01T00:00:00",
        }
    }
    job = usajobs_provider.normalize(raw)
    assert job.source == "usajobs"
    assert job.title == "Software Engineer"
    assert job.company_name == "US Navy"
    assert job.remote is True
    assert job.salary_min == 90000
    assert job.salary_max == 120000
    assert job.salary_currency == "USD"
    assert job.apply_url.startswith("https://www.usajobs.gov")


def test_jsearch_normalize() -> None:
    from app.services.providers.jsearch import jsearch_provider

    raw = {
        "job_id": "999",
        "job_title": "Backend Engineer",
        "employer_name": "FinEdge",
        "job_city": "Mumbai",
        "job_state": "MH",
        "job_country": "India",
        "job_is_remote": False,
        "job_min_salary": 1800000,
        "job_max_salary": 3000000,
        "job_salary_currency": "INR",
        "job_employment_type": "FULLTIME",
        "job_description": "Scale REST APIs.",
        "job_apply_link": "https://jobs.example.com/apply",
        "job_posted_at_datetime_utc": "2026-08-10T10:00:00Z",
    }
    job = jsearch_provider.normalize(raw)
    assert job.source == "jsearch"
    assert job.title == "Backend Engineer"
    assert job.location == "Mumbai, MH"
    assert job.salary_max == 3000000
    assert job.job_type == "full_time"
    assert job.apply_url == "https://jobs.example.com/apply"


def test_remoteok_normalize() -> None:
    from app.services.providers.remoteok import remoteok_provider

    raw = {
        "id": "777",
        "position": "Flutter Developer",
        "company": "Nova",
        "location": "🌏 Worldwide",
        "salary_min": 60000,
        "salary_max": 90000,
        "tags": ["Flutter", "Dart"],
        "date": 1755000000,
        "url": "https://remoteok.com/remote-jobs/777",
        "description": "<p>Build apps</p>",
    }
    job = remoteok_provider.normalize(raw)
    assert job.source == "remoteok"
    assert job.remote is True
    assert job.apply_url == "https://remoteok.com/remote-jobs/777"
    assert job.skills == ["Flutter", "Dart"]
    assert "Build apps" in job.description


def test_greenhouse_normalize() -> None:
    from app.services.providers.greenhouse import greenhouse_provider

    raw = {
        "id": 42,
        "title": "Product Designer",
        "location": {"name": "Remote"},
        "absolute_url": "https://boards.greenhouse.io/acme/jobs/42",
        "content": "<p>Design great products.</p>",
        "metadata": [{"name": "Remote", "value": "Yes"}, {"name": "Employment Type", "value": "Full-time"}],
        "updated_at": "2026-08-09T10:00:00Z",
    }
    job = greenhouse_provider.normalize(raw, "acme")
    assert job.source == "greenhouse"
    assert job.remote is True
    assert job.apply_url == "https://boards.greenhouse.io/acme/jobs/42"
    assert "Design great products" in job.description


def test_ashby_normalize() -> None:
    from app.services.providers.ashby import ashby_provider

    raw = {
        "id": "abc-123",
        "title": "Growth Engineer",
        "locationName": "Remote",
        "employmentType": "Full-time",
        "secondaryLocations": [{"locationName": "San Francisco"}],
    }
    job = ashby_provider.normalize(raw, "Acme")
    assert job.source == "ashby"
    assert job.remote is True
    assert job.apply_url == "https://jobs.ashbyhq.com/acme/abc-123"