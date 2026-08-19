"""Async SQLAlchemy engine and session factory."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import JSON as GenericJSON, CHAR

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def JSONType():
    """JSONB on PostgreSQL, generic JSON on other dialects (SQLite dev)."""
    return JSONB().with_variant(GenericJSON(), "sqlite", "mysql")


def UUIDType():
    """Native UUID on PostgreSQL, CHAR(36) on other dialects."""
    return PG_UUID(as_uuid=False).with_variant(CHAR(36), "sqlite", "mysql")


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and settings.APP_ENV == "development",
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()