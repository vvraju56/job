"""Base adapter contract for job sources."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class NormalizedJob:
    """Canonical job record produced by every source adapter."""

    source: str
    external_id: str
    title: str
    company_name: str
    location: str | None = None
    remote: bool = False
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "INR"
    salary_text: str | None = None
    job_type: str = "full_time"
    level: str = "entry"
    skills: list[str] = field(default_factory=list)
    description: str | None = None
    apply_url: str = ""
    apply_on: str = "Original Website"
    experience_min: int = 0
    experience_max: int = 0
    posted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    company_logo: str | None = None


class BaseAdapter(ABC):
    """Each source implements fetch_latest() and returns NormalizedJob records.

    Adapters never store copyrighted content. They resolve public listing
    metadata and the canonical apply URL so the platform can redirect users
    back to the original portal.
    """

    source_name: str = "base"

    @abstractmethod
    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        """Fetch and normalize recent listings from the source."""
        raise NotImplementedError

    async def search(self, query: str, limit: int = 20) -> list[NormalizedJob]:
        """Default search: fetch latest and filter locally (override per source)."""
        jobs = await self.fetch_latest(limit=limit * 3)
        q = query.lower()
        return [j for j in jobs if q in j.title.lower() or q in j.company_name.lower()][:limit]