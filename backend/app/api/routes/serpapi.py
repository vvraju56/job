"""Multi-source job search, job details, keyless feed, and Developer API endpoints.

Search is registered BEFORE the relational `/jobs/{job_id}` router so
`/jobs/search`, `/jobs/details`, `/jobs/salary`, `/jobs/autocomplete` and
`/jobs/public` are never shadowed by the UUID route.

Routes:
    GET /jobs/search          Multi-source search (cached 6h, quota-tracked)
    GET /jobs/details?id=     Job detail by UUID or provider external id
    GET /jobs/salary          OpenWebNinja salary data (JSearch key, cached)
    GET /jobs/autocomplete    OpenWebNinja web-search suggestions (cached)
    GET /jobs/public          Live keyless feeds: Greenhouse + Ashby + Remote OK
    GET /api/usage            Developer API Dashboard usage summary (admin)
    GET /api/cache-stats      Cache statistics (admin)
    GET /api/health           Provider health (public)
"""
import asyncio
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentAdmin, DbDep
from app.models.models import Job
from app.schemas.schemas import JobList, JobOut, JobSearchParams, UsageOut
from app.services import openwebninja
from app.services.jobs_service import (
    cache_stats,
    configured,
    job_details,
    provider_name,
    search_jobs,
    usage_summary,
)
from app.services.providers import get_provider
from app.services.providers.base import ProviderNotConfigured, QuotaExceeded

search_router = APIRouter(prefix="/jobs", tags=["jobs"])
usage_router = APIRouter(prefix="", tags=["developer"])


async def _db_fallback(params: JobSearchParams, db: AsyncSession) -> JobList:
    """Fallback search over the relational jobs table.

    Used when no provider key is configured (local dev) so the product keeps
    working against previously ingested/aggregated jobs.
    """
    stmt = select(Job).where(Job.active.is_(True))
    if params.q:
        pattern = f"%{params.q}%"
        stmt = stmt.where(
            Job.title.ilike(pattern)
            | Job.company_name.ilike(pattern)
            | Job.description.ilike(pattern)
        )
    if params.location:
        stmt = stmt.where(Job.location.ilike(f"%{params.location}%"))
    if params.remote is not None:
        stmt = stmt.where(Job.remote == params.remote)
    if params.salary_min is not None:
        stmt = stmt.where(Job.salary_max >= params.salary_min)
    if params.salary_max is not None:
        stmt = stmt.where(Job.salary_min <= params.salary_max)
    if params.job_type:
        stmt = stmt.where(Job.job_type == params.job_type)
    if params.level:
        stmt = stmt.where(Job.level == params.level)
    if params.sort == "salary_desc":
        stmt = stmt.order_by(Job.salary_max.desc().nulls_last())
    elif params.sort == "salary_asc":
        stmt = stmt.order_by(Job.salary_min.asc().nulls_last())
    elif params.sort == "relevance" and params.q:
        stmt = stmt.order_by(
            case((Job.title.ilike(f"%{params.q}%"), 1), else_=0).desc(),
            Job.posted_at.desc().nulls_last(),
        )
    else:
        stmt = stmt.order_by(Job.posted_at.desc().nulls_last())

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (
        await db.execute(
            stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
        )
    ).scalars().all()
    return JobList(total=total, page=params.page, page_size=params.page_size, items=list(rows))


@search_router.get("/search", response_model=JobList)
async def search(
    db: DbDep,
    query: str = Query(default="", max_length=200),
    location: str | None = Query(default=None, max_length=200),
    remote: bool | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    job_type: str | None = None,
    level: str | None = None,
    experience: int | None = None,
    date_posted: str | None = None,
    sort: str = "relevance",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> JobList:
    params = JobSearchParams(
        q=query or None,
        location=location,
        remote=remote,
        salary_min=salary_min,
        salary_max=salary_max,
        job_type=job_type,
        level=level,
        experience_min=experience,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    filters = {
        "remote": bool(remote),
        "salary_min": salary_min,
        "job_type": job_type,
        "level": level,
        "experience": experience,
        "date_posted": date_posted,
    }

    try:
        items = await search_jobs(db, query=query, location=location or "", page=page, filters=filters)
        total = len(items)
        return JobList(total=total, page=page, page_size=page_size, items=items)
    except QuotaExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
            headers={"Retry-After": "3600"},
        ) from exc
    except ProviderNotConfigured:
        return await _db_fallback(params, db)


@search_router.get("/details", response_model=JobOut)
async def details(db: DbDep, id: str = Query(min_length=1, max_length=600)) -> Job | dict:
    job = await job_details(db, id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@search_router.get("/salary")
async def salary_data(
    job_title: str = Query(min_length=1, max_length=200),
    location: str | None = Query(default=None, max_length=200),
) -> dict:
    """Live salary data for a job title (OpenWebNinja, uses the JSearch key)."""
    try:
        data, cached = await openwebninja.job_salary(job_title, location or "")
    except ProviderNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Salary provider request failed: {exc}"
        ) from exc
    return {"provider": "openwebninja", "cached": cached, "data": data}


@search_router.get("/autocomplete")
async def autocomplete_suggestions(
    query: str = Query(min_length=1, max_length=200),
) -> dict:
    """Web-search autocomplete suggestions (OpenWebNinja, uses the JSearch key)."""
    try:
        data, cached = await openwebninja.autocomplete(query)
    except ProviderNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Autocomplete provider request failed: {exc}"
        ) from exc
    return {"provider": "openwebninja", "cached": cached, "data": data}


def _public_job_dict(job) -> dict:
    """Serialize a NormalizedJob into a JobOut-shaped dict (no persisted id)."""
    return {
        "id": f"{job.source}:{job.external_id}",
        "source": job.source,
        "title": job.title,
        "description": job.description,
        "company_id": None,
        "company_name": job.company_name,
        "company_logo": job.company_logo,
        "location": job.location,
        "remote": job.remote,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "salary_text": job.salary_text,
        "job_type": job.job_type,
        "level": job.level,
        "skills": job.skills,
        "apply_url": job.apply_url,
        "apply_on": job.apply_on,
        "experience_min": job.experience_min,
        "experience_max": job.experience_max,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "sponsored": False,
        "views": 0,
    }


@search_router.get("/public")
async def public_jobs(
    greenhouse: str = Query(default="stripe", max_length=100),
    ashby: str = Query(default="openai", max_length=100),
) -> dict:
    """Live jobs from the three keyless providers, keyed by provider.

    No API keys are required server-side for these sources. Each provider's
    failures are isolated so one broken board never kills the response.
    """
    names = ["greenhouse", "ashby", "remoteok"]
    boards = {"greenhouse": greenhouse, "ashby": ashby}

    async def _run(name: str) -> list[dict]:
        try:
            provider = get_provider(name)
            jobs = await provider.search(boards.get(name, ""))
            return [_public_job_dict(j) for j in jobs[:20]]
        except Exception:  # noqa: BLE001
            return []

    results = await asyncio.gather(*(_run(n) for n in names))
    return dict(zip(names, results))


@usage_router.get("/usage", response_model=UsageOut)
async def usage(db: DbDep, _: CurrentAdmin) -> dict:
    return await usage_summary(db)


@usage_router.get("/cache-stats")
async def cache_stats_endpoint(_: CurrentAdmin) -> dict:
    stats = cache_stats()
    return {
        "backend": stats.backend,
        "hits": stats.hits,
        "misses": stats.misses,
        "entries": stats.entries,
        "hit_rate": stats.hit_rate,
    }


@usage_router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "provider": provider_name(),
        "provider_configured": configured(),
    }