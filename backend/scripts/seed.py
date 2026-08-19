"""Seed the local/dev database with demo jobs and companies."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.adapters.aggregator import upsert_jobs  # noqa: E402
from app.adapters.sources import (  # noqa: E402
    CompanyAdapter,
    IndeedAdapter,
    InternshalaAdapter,
    LinkedinAdapter,
    NaukriAdapter,
    WellfoundAdapter,
)
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.models import Company  # noqa: E402

DEMO_COMPANIES = [
    dict(name="Nova Labs", slug="nova-labs", industry="SaaS", location="Bengaluru, India", description="Cloud-native SaaS platform for analytics.", size="51-200", rating=4.6, review_count=87, verified=True, website="https://novalabs.example"),
    dict(name="VertexAI", slug="vertexai", industry="Artificial Intelligence", location="Remote", description="Applied AI startup building LLM tooling.", size="11-50", rating=4.8, review_count=42, verified=True, website="https://vertexai.example"),
    dict(name="FinEdge", slug="finedge", industry="Fintech", location="Mumbai, India", description="Digital banking for emerging markets.", size="201-500", rating=4.3, review_count=156, verified=False, website="https://finedge.example"),
    dict(name="PixelCraft", slug="pixelcraft", industry="Design & Media", location="Gurugram, India", description="Design studio and creative agency.", size="11-50", rating=4.4, review_count=63, verified=False, website="https://pixelcraft.example"),
    dict(name="QuantumLabs", slug="quantumlabs", industry="Deep Tech", location="Pune, India", description="Hardware-adjacent deep-tech research lab.", size="501-1000", rating=4.7, review_count=210, verified=True, website="https://quantumlabs.example"),
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        for data in DEMO_COMPANIES:
            existing = (await db.execute(select(Company).where(Company.slug == data["slug"]))).scalar_one_or_none()
            if existing is None:
                db.add(Company(**data))
        await db.commit()

    async with SessionLocal() as db:
        jobs = []
        for adapter in [
            LinkedinAdapter(), IndeedAdapter(), NaukriAdapter(),
            InternshalaAdapter(), WellfoundAdapter(), CompanyAdapter(),
        ]:
            jobs.extend(await adapter.fetch_latest(limit=3))
        count = await upsert_jobs(db, jobs)
        print(f"Seeded {count} demo jobs.")


if __name__ == "__main__":
    asyncio.run(seed())