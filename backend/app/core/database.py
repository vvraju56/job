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


def _async_database_url(url: str) -> str:
    """Coerce a sync Postgres URL to the asyncpg driver.

    Supabase's copyable connection strings use `postgresql://` and commonly
    carry `?sslmode=require`. SQLAlchemy's asyncio extension requires
    `postgresql+asyncpg://` for Postgres and `sqlite+aiosqlite://` for SQLite.
    asyncpg's dialect does not understand the `sslmode` query parameter (it
    raises `TypeError: connect() got an unexpected keyword argument 'sslmode'`),
    so translate `sslmode` to asyncpg's native `ssl=true`.
    """
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
            "postgres://", "postgresql+asyncpg://", 1
        )
        if "sslmode=" in url:
            base, _, query = url.partition("?")
            params = []
            for p in query.split("&"):
                if p.startswith("sslmode="):
                    params.append("ssl=" + p.split("=", 1)[1])
                elif p:
                    params.append(p)
            return base + "?" + "&".join(params)
        return url
    if url.startswith("sqlite://"):
        if url.startswith("sqlite+aiosqlite://") or url.startswith("sqlite+pysqlite://"):
            return url
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


engine = create_async_engine(
    _async_database_url(settings.DATABASE_URL),
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