"""FastAPI application entrypoint."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import admin, auth, companies, jobs, notifications, resume, serpapi, users
from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run schema migrations on startup outside local development.

    Local SQLite (development) is created directly by the ORM, so we skip
    Alembic there to keep `makeable.db` working as-is. On Render (PostgreSQL)
    `alembic upgrade head` applies 0001 + 0002 before serving traffic.
    """
    if settings.APP_ENV != "development" and not settings.DATABASE_URL.startswith("sqlite"):
        from alembic import command
        from alembic.config import Config

        await asyncio.to_thread(command.upgrade, Config("alembic.ini"), "head")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Makeable Jobs aggregation API. Searches across multiple job portals "
        "and redirects users to the original application page. "
        "One Search. Every Opportunity."
    ),
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

# /jobs/search and /jobs/details MUST be registered before jobs.router
# (which owns the catch-all `/jobs/{job_id}` route).
for route in (auth.router, serpapi.search_router, jobs.router, companies.router, users.router, resume.router, notifications.router, admin.router, serpapi.usage_router):
    app.include_router(route, prefix=API_PREFIX)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {"name": settings.APP_NAME, "tagline": "One Search. Every Opportunity.", "docs": "/docs"}