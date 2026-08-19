"""Job search/filter/save tests."""
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.adapters.base import NormalizedJob
from app.adapters.aggregator import upsert_jobs
from app.core.database import SessionLocal
from app.models.models import Job

SAMPLE_JOBS = [
    NormalizedJob(
        source="linkedin",
        external_id="t-1",
        title="Senior Flutter Developer",
        company_name="Nova Labs",
        location="Bengaluru, India",
        remote=True,
        salary_min=1_800_000,
        salary_max=3_000_000,
        salary_text="₹18L – ₹30L/yr",
        job_type="full_time",
        level="senior",
        skills=["Flutter", "Dart", "Firebase"],
        description="Build cross-platform apps with Flutter.",
        apply_url="https://linkedin.com/jobs/view/1",
        apply_on="LinkedIn",
        experience_min=4,
        experience_max=7,
    ),
    NormalizedJob(
        source="internshala",
        external_id="t-2",
        title="Software Engineering Intern",
        company_name="Nova Labs",
        location="Remote",
        remote=True,
        salary_min=20_000,
        salary_max=30_000,
        job_type="internship",
        level="entry",
        skills=["Python"],
        description="Paid internship with mentorship.",
        apply_url="https://internshala.com/internship/2",
        apply_on="Internshala",
        experience_min=0,
        experience_max=0,
    ),
    NormalizedJob(
        source="indeed",
        external_id="t-3",
        title="Backend Engineer",
        company_name="FinEdge",
        location="Mumbai, India",
        remote=False,
        salary_min=1_500_000,
        salary_max=2_400_000,
        job_type="full_time",
        level="mid",
        skills=["Python", "FastAPI"],
        description="Scale REST APIs.",
        apply_url="https://in.indeed.com/viewjob/3",
        apply_on="Indeed",
        experience_min=3,
        experience_max=6,
    ),
]


@pytest_asyncio.fixture(autouse=True)
async def _seed_jobs() -> None:
    async with SessionLocal() as db:
        existing = (await db.execute(select(Job))).scalars().all()
        for job in existing:
            await db.delete(job)
        await db.commit()
        await upsert_jobs(db, SAMPLE_JOBS)


async def test_search_all_jobs(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


async def test_search_by_query(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/", params={"q": "Flutter"})
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Senior Flutter Developer"


async def test_filter_remote(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/", params={"remote": "true"})
    data = resp.json()
    assert data["total"] == 2


async def test_filter_salary(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/", params={"salary_min": 1_000_000})
    data = resp.json()
    assert data["total"] == 2
    resp2 = await client.get("/api/v1/jobs/", params={"salary_max": 500_000})
    assert resp2.json()["total"] == 1


async def test_filter_experience(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/", params={"experience_min": 4})
    data = resp.json()
    # Jobs whose max experience accommodates a 4+ year candidate (intern max 0 excluded).
    assert data["total"] == 2
    assert all(item["experience_max"] >= 4 for item in data["items"])


async def test_filter_job_type(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/", params={"job_type": "internship"})
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["source"] == "internshala"


async def test_filter_company(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/", params={"company": "Nova"})
    data = resp.json()
    assert data["total"] == 2


async def test_sort_salary_desc(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/", params={"sort": "salary_desc"})
    salaries = [item["salary_max"] for item in resp.json()["items"]]
    assert salaries == sorted(salaries, reverse=True)


async def test_trending_and_similar(client: AsyncClient) -> None:
    trending = await client.get("/api/v1/jobs/trending")
    assert trending.status_code == 200
    jobs = trending.json()
    assert len(jobs) == 3

    job_id = jobs[0]["id"]
    similar = await client.get(f"/api/v1/jobs/{job_id}/similar")
    assert similar.status_code == 200


async def test_job_detail_increments_views(client: AsyncClient) -> None:
    jobs = (await client.get("/api/v1/jobs/")).json()["items"]
    job_id = jobs[0]["id"]
    first = await client.get(f"/api/v1/jobs/{job_id}")
    second = await client.get(f"/api/v1/jobs/{job_id}")
    assert second.json()["views"] == first.json()["views"] + 1


async def test_save_and_unsave_job(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    job_id = (await client.get("/api/v1/jobs/")).json()["items"][0]["id"]

    save = await client.post(f"/api/v1/jobs/{job_id}/save", headers=auth_headers)
    assert save.status_code == 201
    assert save.json()["saved"] is True

    saved = await client.get("/api/v1/users/me/saved-jobs", headers=auth_headers)
    assert len(saved.json()["jobs"]) == 1

    unsave = await client.delete(f"/api/v1/jobs/{job_id}/save", headers=auth_headers)
    assert unsave.status_code == 204

    saved = await client.get("/api/v1/users/me/saved-jobs", headers=auth_headers)
    assert len(saved.json()["jobs"]) == 0


async def test_apply_tracking(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    job = (await client.get("/api/v1/jobs/")).json()["items"][0]
    resp = await client.post(
        "/api/v1/users/me/applications",
        json={
            "job_id": job["id"],
            "company_name": job["company_name"],
            "role": job["title"],
            "applied_url": job["apply_url"],
            "status": "applied",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    app_id = resp.json()["id"]

    apps = await client.get("/api/v1/users/me/applications", headers=auth_headers)
    assert len(apps.json()["applications"]) == 1

    update = await client.patch(
        f"/api/v1/users/me/applications/{app_id}",
        json={"status": "interviewing"},
        headers=auth_headers,
    )
    assert update.json()["status"] == "interviewing"