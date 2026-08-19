"""Shared fixtures for the test suite.

We use an isolated temp SQLite database per session so tests never touch
the local dev database (makeable.db).
"""
import os
import tempfile
from collections.abc import AsyncIterator

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{tempfile.mkdtemp()}/test_makeable.db")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import Base, engine
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="session")
async def tester_tokens() -> dict[str, str]:
    """Register/login the shared tester account once per session."""
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.models import User as U

    email = "tester@example.com"
    password = "password123"

    async with SessionLocal() as db:
        existing = (await db.execute(select(U).where(U.email == email))).scalar_one_or_none()
    if existing is None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/api/v1/auth/register",
                json={"name": "Test User", "email": email, "password": password},
            )
            assert resp.status_code == 201, resp.text
            token = resp.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers(tester_tokens: dict[str, str]) -> dict[str, str]:
    return tester_tokens