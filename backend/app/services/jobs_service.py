"""Job service: usage summaries for the Developer API Dashboard.

Search orchestration now lives in `services/aggregator.py` (multi-provider
fan-out, dedupe, caching). This module keeps the dashboard metrics.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import ApiLog, Job
from app.services.aggregator import (
    cache_stats,
    log_search,
    search_aggregated,
    searches_used,
)
from app.services.providers.base import ProviderNotConfigured, QuotaExceeded  # noqa: F401 (re-export)

__all__ = ["cache_stats", "search_aggregated", "searches_used", "log_search"]


async def search_jobs(
    db: AsyncSession,
    query: str,
    location: str = "",
    page: int = 1,
    filters: dict | None = None,
):
    """Compatibility wrapper — routes to the multi-source aggregator."""
    return await search_aggregated(db, query=query, location=location, page=page, filters=filters)


async def job_details(db: AsyncSession, job_id: str) -> Job | dict | None:
    """Resolve a job by UUID or source external id.

    Auto-details: when the job is not persisted locally, fetch the full
    record live from the provider using its API key (JSearch/OpenWebNinja,
    USAJobs, Greenhouse, Remote OK). Accepts either a bare external id or
    the `source:external_id` format used by the public keyless feed.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is not None:
        return job
    result = await db.execute(
        select(Job).where(Job.external_id == job_id).limit(1)
    )
    job = result.scalar_one_or_none()
    if job is not None:
        return job

    from app.services.providers import get_provider

    # `source:external_id` form → live fetch from that provider.
    if ":" in job_id:
        source, _, external_id = job_id.partition(":")
        try:
            provider = get_provider(source)
        except KeyError:
            return None
        if provider.configured:
            live = await provider.get_job(external_id, company=_company_hint(source, external_id))
            if live is not None:
                return _normalized_to_out(live)
        return None

    # Bare external id → try every enabled provider.
    from app.services.providers import get_enabled_providers

    for provider in get_enabled_providers():
        if not provider.configured:
            continue
        live = await provider.get_job(job_id)
        if live is not None:
            return _normalized_to_out(live)
    return None


def _company_hint(source: str, external_id: str) -> str | None:
    """Company-board providers need the board slug, which the detail id does
    not carry — return None so Greenhouse/Ashby fall through gracefully."""
    return None


def _normalized_to_out(job) -> dict:
    """Shape a live NormalizedJob into a JobOut-compatible dict (no persisted id)."""
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
        "experience_min": 0,
        "experience_max": 0,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "sponsored": False,
        "views": 0,
    }


async def usage_summary(db: AsyncSession) -> dict:
    """Numbers for the Developer API Dashboard."""
    used = await searches_used(db)
    limit = settings.SERPAPI_MONTHLY_LIMIT

    total_logs = int(
        (await db.execute(select(func.count()).select_from(ApiLog))).scalar_one()
    )
    cached_logs = int(
        (
            await db.execute(
                select(func.count())
                .select_from(ApiLog)
                .where(ApiLog.cached.is_(True))
            )
        ).scalar_one()
    )
    hit_rate = round(cached_logs / total_logs * 100, 1) if total_logs else 0.0

    recent = (
        await db.execute(
            select(ApiLog)
            .order_by(ApiLog.created_at.desc())
            .limit(20)
        )
    ).scalars().all()

    recent_payload = [
        {
            "endpoint": log.endpoint,
            "query": log.query,
            "location": log.location,
            "page": log.page,
            "response_time_ms": log.response_time_ms,
            "cached": log.cached,
            "status_code": log.status_code,
            "timestamp": log.created_at.isoformat(),
        }
        for log in recent
    ]

    cache = cache_stats()

    return {
        "searches_used": used,
        "monthly_limit": limit,
        "remaining": max(0, limit - used),
        "cache_hit_rate": hit_rate,
        "total_requests": total_logs,
        "cache": {
            "backend": cache.backend,
            "hits": cache.hits,
            "misses": cache.misses,
            "entries": cache.entries,
            "hit_rate": cache.hit_rate,
        },
        "provider": {
            "name": provider_name(),
            "configured": configured(),
        },
        "recent_searches": recent_payload,
    }


def provider_name() -> str:
    from app.services.providers import get_provider

    try:
        return get_provider().name
    except KeyError:
        return settings.JOB_PROVIDER


def configured() -> bool:
    from app.services.providers import get_provider

    try:
        return get_provider().configured
    except KeyError:
        return False