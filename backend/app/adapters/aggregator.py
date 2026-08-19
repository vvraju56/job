"""Adapter registry and ingestion coordinator."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseAdapter, NormalizedJob
from app.adapters.sources import (
    CompanyAdapter,
    IndeedAdapter,
    InternshalaAdapter,
    LinkedinAdapter,
    NaukriAdapter,
    WellfoundAdapter,
)
from app.models.models import Job

logger = logging.getLogger(__name__)

ADAPTERS: dict[str, BaseAdapter] = {
    adapter.source_name: adapter
    for adapter in [
        LinkedinAdapter(),
        IndeedAdapter(),
        NaukriAdapter(),
        InternshalaAdapter(),
        WellfoundAdapter(),
        CompanyAdapter(),
    ]
}


async def run_ingestion(db: AsyncSession, sources: list[str] | None = None, limit: int = 50) -> dict[str, int]:
    """Fetch jobs from enabled adapters and upsert normalized records."""
    names = sources or list(ADAPTERS)
    results: dict[str, int] = {}
    for name in names:
        adapter = ADAPTERS.get(name)
        if adapter is None:
            continue
        try:
            jobs = await adapter.fetch_latest(limit=limit)
            count = await upsert_jobs(db, jobs)
            results[name] = count
            logger.info("Ingested %d jobs from %s", count, name)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Adapter %s failed: %s", name, exc)
            results[name] = 0
    return results


async def upsert_jobs(db: AsyncSession, jobs: list[NormalizedJob]) -> int:
    count = 0
    for item in jobs:
        existing = (
            await db.execute(
                select(Job).where(Job.external_id == item.external_id, Job.source == item.source)
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.add(Job(
            external_id=item.external_id,
            source=item.source,
            title=item.title,
            description=item.description,
            company_name=item.company_name,
            company_logo=item.company_logo,
            location=item.location,
            remote=item.remote,
            salary_min=item.salary_min,
            salary_max=item.salary_max,
            salary_currency=item.salary_currency,
            salary_text=item.salary_text,
            job_type=item.job_type,
            level=item.level,
            skills=item.skills,
            apply_url=item.apply_url,
            apply_on=item.apply_on,
            experience_min=item.experience_min,
            experience_max=item.experience_max,
            posted_at=item.posted_at,
            active=True,
        ))
        count += 1
    await db.commit()
    return count