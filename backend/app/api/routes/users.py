"""User profile, saved jobs, applications, searches, preferences."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbDep
from app.models.models import Application, Job, SavedJob, Search, User
from app.schemas.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationsOut,
    ApplicationStatusUpdate,
    JobOut,
    PreferencesUpdate,
    SavedJobsOut,
    SearchOut,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(db: DbDep, user: CurrentUser, payload: UserUpdate) -> User:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/me/preferences", response_model=UserOut)
async def update_preferences(db: DbDep, user: CurrentUser, payload: PreferencesUpdate) -> User:
    user.preferences = payload.model_dump()
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me/saved-jobs", response_model=SavedJobsOut)
async def saved_jobs(db: DbDep, user: CurrentUser) -> dict:
    result = await db.execute(
        select(Job)
        .join(SavedJob, SavedJob.job_id == Job.id)
        .where(SavedJob.user_id == user.id, Job.active.is_(True))
        .order_by(SavedJob.created_at.desc())
    )
    return {"jobs": list(result.scalars().all())}


@router.get("/me/applications", response_model=ApplicationsOut)
async def applications(db: DbDep, user: CurrentUser, status_filter: str | None = None) -> dict:
    stmt = select(Application).where(Application.user_id == user.id)
    if status_filter:
        stmt = stmt.where(Application.status == status_filter)
    result = await db.execute(stmt.order_by(Application.applied_at.desc()))
    return {"applications": list(result.scalars().all())}


@router.post("/me/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(db: DbDep, user: CurrentUser, payload: ApplicationCreate) -> Application:
    app = Application(user_id=user.id, **payload.model_dump(exclude_none=True))
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


@router.patch("/me/applications/{app_id}", response_model=ApplicationOut)
async def update_application(db: DbDep, user: CurrentUser, app_id: str, payload: ApplicationStatusUpdate) -> Application:
    result = await db.execute(select(Application).where(Application.id == app_id, Application.user_id == user.id))
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    app.status = payload.status
    if payload.notes is not None:
        app.notes = payload.notes
    await db.commit()
    await db.refresh(app)
    return app


@router.delete("/me/applications/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(db: DbDep, user: CurrentUser, app_id: str) -> None:
    result = await db.execute(select(Application).where(Application.id == app_id, Application.user_id == user.id))
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    await db.delete(app)
    await db.commit()


@router.get("/me/searches", response_model=list[SearchOut])
async def recent_searches(db: DbDep, user: CurrentUser, limit: int = Query(10, ge=1, le=50)) -> list[Search]:
    result = await db.execute(
        select(Search)
        .where(Search.user_id == user.id)
        .order_by(Search.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())