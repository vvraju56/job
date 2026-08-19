"""Company list, detail, and admin management."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentAdmin, DbDep
from app.models.models import Company, Job
from app.schemas.schemas import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


async def _company_out(db: AsyncSession, company: Company) -> CompanyOut:
    count = (
        await db.execute(select(func.count()).select_from(Job).where(Job.company_id == company.id, Job.active.is_(True)))
    ).scalar_one()
    out = CompanyOut.model_validate(company)
    out.open_positions = count
    return out


@router.get("/", response_model=list[CompanyOut])
async def list_companies(
    db: DbDep,
    search: str | None = None,
    limit: int = Query(24, ge=1, le=100),
) -> list[CompanyOut]:
    stmt = select(Company)
    if search:
        stmt = stmt.where(Company.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(Company.verified.desc(), Company.review_count.desc()).limit(limit)
    result = await db.execute(stmt)
    companies = list(result.scalars().all())
    return [await _company_out(db, c) for c in companies]


@router.get("/featured", response_model=list[CompanyOut])
async def featured_companies(db: DbDep, limit: int = Query(6, ge=1, le=30)) -> list[CompanyOut]:
    stmt = (
        select(Company)
        .join(Job, Job.company_id == Company.id, isouter=True)
        .where(Job.active.is_(True))
        .group_by(Company.id)
        .order_by(func.count(Job.id).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    companies = list(result.scalars().all())
    return [await _company_out(db, c) for c in companies]


@router.get("/{slug}", response_model=CompanyOut)
async def company_detail(db: DbDep, slug: str) -> CompanyOut:
    result = await db.execute(select(Company).where(Company.slug == slug))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return await _company_out(db, company)


@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(db: DbDep, _admin: CurrentAdmin, payload: CompanyCreate) -> CompanyOut:
    company = Company(**payload.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return await _company_out(db, company)


@router.patch("/{slug}", response_model=CompanyOut)
async def update_company(db: DbDep, _admin: CurrentAdmin, slug: str, payload: CompanyUpdate) -> CompanyOut:
    result = await db.execute(select(Company).where(Company.slug == slug))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    await db.commit()
    await db.refresh(company)
    return await _company_out(db, company)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(db: DbDep, _admin: CurrentAdmin, slug: str) -> None:
    result = await db.execute(select(Company).where(Company.slug == slug))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await db.delete(company)
    await db.commit()