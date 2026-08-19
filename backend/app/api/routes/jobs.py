"""Job listing, search, details, save, trending, recommended."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbDep
from app.models.models import Job, SavedJob, Search
from app.schemas.schemas import JobList, JobOut, JobSearchParams, SavedJobCreate

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _apply_filters(stmt, p: JobSearchParams):
    if p.q:
        pattern = f"%{p.q}%"
        stmt = stmt.where(
            Job.title.ilike(pattern)
            | Job.company_name.ilike(pattern)
            | Job.description.ilike(pattern)
        )
    if p.location:
        stmt = stmt.where(Job.location.ilike(f"%{p.location}%"))
    if p.remote is not None:
        stmt = stmt.where(Job.remote == p.remote)
    if p.salary_min is not None:
        stmt = stmt.where(Job.salary_max >= p.salary_min)
    if p.salary_max is not None:
        stmt = stmt.where(Job.salary_min <= p.salary_max)
    if p.job_type:
        stmt = stmt.where(Job.job_type == p.job_type)
    if p.level:
        stmt = stmt.where(Job.level == p.level)
    if p.experience_min is not None:
        stmt = stmt.where(Job.experience_max >= p.experience_min)
    if p.experience_max is not None:
        stmt = stmt.where(Job.experience_min <= p.experience_max)
    if p.source:
        stmt = stmt.where(Job.source == p.source)
    if p.company:
        stmt = stmt.where(Job.company_name.ilike(f"%{p.company}%"))
    return stmt


@router.get("/", response_model=JobList)
async def search_jobs(
    db: DbDep,
    q: Annotated[str | None, Query(max_length=200)] = None,
    location: str | None = None,
    remote: bool | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    job_type: str | None = None,
    level: str | None = None,
    experience_min: int | None = None,
    experience_max: int | None = None,
    source: str | None = None,
    company: str | None = None,
    sort: str = "recent",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> JobList:
    params = JobSearchParams(
        q=q, location=location, remote=remote, salary_min=salary_min, salary_max=salary_max,
        job_type=job_type, level=level, experience_min=experience_min,
        experience_max=experience_max, source=source, company=company, sort=sort,
        page=page, page_size=page_size,
    )
    base = _apply_filters(select(Job).where(Job.active.is_(True)), params)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    if sort == "salary_desc":
        base = base.order_by(Job.salary_max.desc().nulls_last())
    elif sort == "salary_asc":
        base = base.order_by(Job.salary_min.asc().nulls_last())
    elif sort == "relevance" and params.q:
        base = base.order_by(
            case((Job.title.ilike(f"%{params.q}%"), 1), else_=0).desc(),
            Job.posted_at.desc().nulls_last(),
        )
    else:
        base = base.order_by(Job.posted_at.desc().nulls_last())

    items = (
        await db.execute(
            base.offset((params.page - 1) * params.page_size).limit(params.page_size)
        )
    ).scalars().all()

    return JobList(total=total, page=params.page, page_size=params.page_size, items=list(items))


@router.get("/trending", response_model=list[JobOut])
async def trending_jobs(db: DbDep, limit: int = Query(6, ge=1, le=30)) -> list[Job]:
    result = await db.execute(
        select(Job)
        .where(Job.active.is_(True))
        .order_by(Job.views.desc(), Job.posted_at.desc().nulls_last())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/recommended", response_model=list[JobOut])
async def recommended_jobs(db: DbDep, user: CurrentUser, limit: int = Query(8, ge=1, le=30)) -> list[Job]:
    keywords = user.skills or []
    prefs = user.preferences or {}
    pref_keywords = prefs.get("keywords", [])
    terms = [t for t in (keywords + pref_keywords) if t]
    stmt = select(Job).where(Job.active.is_(True))
    if terms:
        clause = Job.company_name.ilike(f"%{terms[0]}%")
        for t in terms[1:]:
            clause = clause | Job.company_name.ilike(f"%{t}%")
        stmt = stmt.where(clause)
    if prefs.get("remote_only"):
        stmt = stmt.where(Job.remote.is_(True))
    result = await db.execute(stmt.order_by(Job.posted_at.desc().nulls_last()).limit(limit))
    return list(result.scalars().all())


@router.get("/search-suggestions", response_model=list[str])
async def search_suggestions(db: DbDep, q: str = Query(min_length=1, max_length=100), limit: int = Query(8, ge=1, le=20)) -> list[str]:
    result = await db.execute(
        select(Job.title)
        .where(Job.title.ilike(f"%{q}%"))
        .group_by(Job.title)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{job_id}", response_model=JobOut)
async def job_detail(db: DbDep, job_id: str) -> Job:
    result = await db.execute(select(Job).where(Job.id == job_id, Job.active.is_(True)))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job.views += 1
    await db.commit()
    return job


@router.post("/{job_id}/save", status_code=status.HTTP_201_CREATED)
async def save_job(db: DbDep, user: CurrentUser, job_id: str) -> dict:
    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    existing = (
        await db.execute(select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id))
    ).scalar_one_or_none()
    if existing is not None:
        return {"saved": True}
    db.add(SavedJob(user_id=user.id, job_id=job_id))
    await db.commit()
    return {"saved": True}


@router.delete("/{job_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(db: DbDep, user: CurrentUser, job_id: str) -> None:
    existing = (
        await db.execute(select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id))
    ).scalar_one_or_none()
    if existing is not None:
        await db.delete(existing)
        await db.commit()


@router.get("/{job_id}/similar", response_model=list[JobOut])
async def similar_jobs(db: DbDep, job_id: str, limit: int = Query(5, ge=1, le=20)) -> list[Job]:
    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    stmt = (
        select(Job)
        .where(Job.active.is_(True), Job.id != job_id, Job.title.ilike(f"%{job.title.split()[-1]}%"))
        .order_by(Job.posted_at.desc().nulls_last())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/track-search", status_code=status.HTTP_201_CREATED)
async def track_search(
    db: DbDep,
    user: CurrentUser,
    q: str = Query(min_length=1, max_length=200),
    filters: str = "{}",
) -> dict:
    import json as _json

    try:
        parsed = _json.loads(filters)
    except _json.JSONDecodeError:
        parsed = {}
    db.add(Search(user_id=user.id, query=q, filters=parsed, result_count=0))
    await db.commit()
    return {"tracked": True}