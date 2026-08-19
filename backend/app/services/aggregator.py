"""Multi-source search aggregator.

Fans a search out to every enabled provider (SerpApi, USAJobs, JSearch,
Greenhouse, Ashby, Remote OK) concurrently, merges the normalized results,
removes duplicates across sources, persists them into `jobs`, and serves
identical searches from the Redis cache for 6 hours.

Dedup rule: same (title, company, location, apply URL) from multiple sources
keeps the higher-priority source (SerpApi > JSearch > Greenhouse > Ashby >
USAJobs > Remote OK).
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.aggregator import upsert_jobs
from app.adapters.base import NormalizedJob
from app.core.config import settings
from app.models.models import ApiLog, Job
from app.schemas.schemas import JobOut
from app.services.cache import CacheStats, cache_key, cache_service
from app.services.providers import SEARCH_PRIORITY, get_enabled_providers
from app.services.providers.base import (
    DEFAULT_LOCATION,
    JobFilters,
    ProviderNotConfigured,
    QuotaExceeded,
)


def _month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def searches_used(db: AsyncSession) -> int:
    """Non-cached SerpApi searches this month (the quota-consuming ones)."""
    result = await db.execute(
        select(func.count())
        .select_from(ApiLog)
        .where(
            ApiLog.endpoint == "/jobs/search",
            ApiLog.cached.is_(False),
            ApiLog.created_at >= _month_start(),
        )
    )
    return int(result.scalar_one())


async def log_search(
    db: AsyncSession,
    *,
    endpoint: str,
    query: str | None,
    location: str | None,
    page: int,
    response_time_ms: int,
    cached: bool,
    status_code: int,
) -> None:
    db.add(
        ApiLog(
            endpoint=endpoint,
            query=query,
            location=location,
            page=page,
            response_time_ms=response_time_ms,
            cached=cached,
            status_code=status_code,
        )
    )
    await db.commit()


def _to_out(items: list[NormalizedJob] | list[Job]) -> list[JobOut]:
    return [JobOut.model_validate(item) for item in items]


def _dedupe_key(job: NormalizedJob) -> tuple:
    base = (
        job.title.lower().strip(),
        job.company_name.lower().strip(),
        (job.location or "").lower().strip(),
    )
    if job.apply_url:
        return (*base, job.apply_url.lower().strip())
    return (*base, job.source, job.external_id)


def dedupe_jobs(jobs: list[NormalizedJob], priority: list[str]) -> list[NormalizedJob]:
    """Keep the highest-priority source for each unique posting."""
    order = {name: i for i, name in enumerate(priority)}
    by_name = sorted(jobs, key=lambda j: order.get(j.source, 999))
    seen: set[tuple] = set()
    result: list[NormalizedJob] = []
    for job in by_name:
        key = _dedupe_key(job)
        if key in seen:
            continue
        seen.add(key)
        result.append(job)
    return result


def _apply_universal_filters(jobs: list[NormalizedJob], filters: JobFilters) -> list[NormalizedJob]:
    remote = bool(filters.get("remote"))
    salary_min = filters.get("salary_min")
    salary_max = filters.get("salary_max")
    job_type = filters.get("job_type")
    level = filters.get("level")

    kept: list[NormalizedJob] = []
    for job in jobs:
        if remote and not job.remote:
            continue
        if salary_min is not None and job.salary_max is not None and job.salary_max < salary_min:
            continue
        if salary_max is not None and job.salary_min is not None and job.salary_min > salary_max:
            continue
        if job_type and job.job_type != job_type:
            continue
        if level and job.level != level:
            continue
        kept.append(job)
    return kept


async def _run_providers(
    providers,
    query: str,
    location: str,
    page: int,
    filters: JobFilters,
) -> list[NormalizedJob]:
    company = filters.get("company")
    tasks = []
    for provider in providers:
        if not provider.configured:
            continue
        if provider.supports_query_search:
            tasks.append(provider.search(query, location, page, filters))
        elif company:
            tasks.append(
                provider.search(
                    query or str(company), location, page, {**filters, "company": company}
                )
            )

    if not tasks:
        return []

    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[NormalizedJob] = []
    for res in results:
        if isinstance(res, BaseException):
            continue
        jobs.extend(res or [])
    return jobs


async def search_aggregated(
    db: AsyncSession,
    query: str,
    location: str = DEFAULT_LOCATION,
    page: int = 1,
    filters: JobFilters | None = None,
) -> list[JobOut]:
    """Aggregate search across enabled providers with cache + usage logging."""
    filters = filters or {}
    started = time.perf_counter()
    providers = get_enabled_providers()
    provider_names = ",".join(sorted(p.name for p in providers))
    key = cache_key(query, location, page, {**filters, "_providers": provider_names})

    # 1. Cache hit — no upstream calls, still logged for dashboard metrics.
    cached_payload = await cache_service.get(key)
    if cached_payload is not None:
        result = await db.execute(
            select(Job).where(Job.id.in_(cached_payload), Job.active.is_(True))
        )
        rows = list(result.scalars().all())
        if rows:
            elapsed = int((time.perf_counter() - started) * 1000)
            await log_search(
                db, endpoint="/jobs/search", query=query, location=location,
                page=page, response_time_ms=elapsed, cached=True, status_code=200,
            )
            return _to_out(rows)

    # 1b. Nothing configured → let the router serve the relational fallback.
    if not any(p.configured for p in providers):
        raise ProviderNotConfigured("No job provider is configured on the server.")

    # 2. Enforce the SerpApi monthly budget before hitting upstreams.
    serpapi = next((p for p in providers if p.name == "serpapi"), None)
    if serpapi is not None and serpapi.configured:
        if await searches_used(db) >= settings.SERPAPI_MONTHLY_LIMIT:
            await log_search(
                db, endpoint="/jobs/search", query=query, location=location,
                page=page, response_time_ms=int((time.perf_counter() - started) * 1000),
                cached=False, status_code=429,
            )
            raise QuotaExceeded("SerpApi monthly search quota exhausted.")

    # 3. Fan out to providers concurrently.
    jobs = await _run_providers(providers, query, location, page, filters)
    jobs = _apply_universal_filters(jobs, filters)
    jobs = dedupe_jobs(jobs, SEARCH_PRIORITY)

    # 4. Persist and re-read real rows.
    if jobs:
        await upsert_jobs(db, jobs)
        conditions = [
            and_(Job.source == j.source, Job.external_id == j.external_id) for j in jobs
        ]
        result = await db.execute(
            select(Job).where(or_(*conditions), Job.active.is_(True))
        )
        rows = list(result.scalars().all())
    else:
        rows = []

    # 5. Cache returned job IDs for 6 hours.
    if rows:
        await cache_service.set(key, [str(r.id) for r in rows])

    elapsed = int((time.perf_counter() - started) * 1000)
    await log_search(
        db, endpoint="/jobs/search", query=query, location=location, page=page,
        response_time_ms=elapsed, cached=False, status_code=200,
    )
    return _to_out(rows)


def cache_stats() -> CacheStats:
    return cache_service.stats()