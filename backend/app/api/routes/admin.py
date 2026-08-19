"""Admin routes: user management, moderation, analytics, notifications."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentAdmin, DbDep
from app.models.models import Application, Company, Job, Notification, SavedJob, Search, User
from app.schemas.schemas import AnalyticsOut, CompanyCreate, JobCreate, JobOut, NotificationOut, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics", response_model=AnalyticsOut)
async def analytics(db: DbDep, _admin: CurrentAdmin) -> AnalyticsOut:
    active_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_jobs = (await db.execute(select(func.count()).select_from(Job).where(Job.active.is_(True)))).scalar_one()
    total_searches = (await db.execute(select(func.count()).select_from(Search))).scalar_one()
    total_saved = (await db.execute(select(func.count()).select_from(SavedJob))).scalar_one()
    total_apps = (await db.execute(select(func.count()).select_from(Application))).scalar_one()

    popular = (
        await db.execute(
            select(Job.company_name, func.count(Job.id).label("count"))
            .where(Job.active.is_(True))
            .group_by(Job.company_name)
            .order_by(func.count(Job.id).desc())
            .limit(8)
        )
    ).all()
    by_source = (
        await db.execute(
            select(Job.source, func.count(Job.id).label("count"))
            .group_by(Job.source)
            .order_by(func.count(Job.id).desc())
        )
    ).all()

    return AnalyticsOut(
        active_users=active_users,
        total_jobs=total_jobs,
        total_searches=total_searches,
        total_saved_jobs=total_saved,
        total_applications=total_apps,
        popular_companies=[{"name": name, "count": count} for name, count in popular],
        jobs_by_source=[{"source": source, "count": count} for source, count in by_source],
    )


@router.get("/users", response_model=list[UserOut])
async def list_users(db: DbDep, _admin: CurrentAdmin, limit: int = 100) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    return list(result.scalars().all())


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def set_role(db: DbDep, _admin: CurrentAdmin, user_id: str, role: str) -> User:
    if role not in ("user", "admin"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(db: DbDep, _admin: CurrentAdmin, payload: JobCreate) -> Job:
    job = Job(**payload.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.patch("/jobs/{job_id}/moderate", response_model=JobOut)
async def moderate_job(db: DbDep, _admin: CurrentAdmin, job_id: str, active: bool) -> Job:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job.active = active
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/companies", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_company_admin(db: DbDep, _admin: CurrentAdmin, payload: CompanyCreate) -> dict:
    company = Company(**payload.model_dump())
    db.add(company)
    await db.commit()
    return {"created": True}


@router.post("/broadcast", status_code=status.HTTP_201_CREATED)
async def broadcast(db: DbDep, _admin: CurrentAdmin, title: str, body: str | None = None) -> dict:
    result = await db.execute(select(User.id))
    user_ids = list(result.scalars().all())
    for uid in user_ids:
        db.add(Notification(user_id=uid, title=title, body=body, data={"broadcast": True}))
    await db.commit()
    return {"sent": len(user_ids)}