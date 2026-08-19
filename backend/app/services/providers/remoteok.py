"""Remote OK provider (remote-first jobs, keyless).

Remote OK exposes the full feed as a JSON array (first element is metadata).
There is no keyword search param, so results are filtered locally against the
query in the title, company and tags. All jobs are remote.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.adapters.base import NormalizedJob
from app.services.providers.base import (
    DEFAULT_LOCATION,
    JobFilters,
    JobProvider,
    strip_html,
)

API_URL = "https://remoteok.com/api"


class RemoteOKProvider(JobProvider):
    """Remote-first job feed adapter (no API key)."""

    name = "remoteok"

    @property
    def configured(self) -> bool:
        return True  # public feed, no key required

    async def search(
        self,
        query: str,
        location: str = DEFAULT_LOCATION,
        page: int = 1,
        filters: JobFilters | None = None,
    ) -> list[NormalizedJob]:
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                resp = await client.get(API_URL, headers={"User-Agent": "MakeableJobs/1.0"})
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return []

        if not isinstance(data, list):
            return []

        jobs = [entry for entry in data if isinstance(entry, dict) and "position" in entry]

        q = (query or "").lower()
        remote_only = bool((filters or {}).get("remote"))
        result = []
        for entry in jobs:
            job = self.normalize(entry)
            if remote_only and not job.remote:
                continue
            if q:
                haystack = f"{job.title} {job.company_name} {' '.join(job.skills)}".lower()
                tokens = [t for t in q.split() if t]
                if tokens and not all(t in haystack for t in tokens):
                    continue
            result.append(job)

        # Filter first, then page locally over the matching subset.
        start = (max(1, page) - 1) * 20
        return result[start : start + 20]

    async def get_job(self, external_id: str, company: str | None = None) -> NormalizedJob | None:
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                resp = await client.get(API_URL, headers={"User-Agent": "MakeableJobs/1.0"})
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return None

        if not isinstance(data, list):
            return None
        for entry in data:
            if isinstance(entry, dict) and "position" in entry and str(entry.get("id") or "") == external_id:
                return self.normalize(entry)
        return None

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        salary_min = raw.get("salary_min") or 0
        salary_max = raw.get("salary_max") or 0
        salary_min = salary_min if salary_min > 0 else None
        salary_max = salary_max if salary_max > 0 else None

        posted_ts = raw.get("date")
        posted_at = None
        if posted_ts:
            try:
                posted_at = datetime.fromtimestamp(int(posted_ts), tz=timezone.utc)
            except (ValueError, OSError, TypeError):
                posted_at = None

        return NormalizedJob(
            source=self.name,
            external_id=str(raw.get("id") or ""),
            title=raw.get("position") or "Untitled",
            company_name=raw.get("company") or "Unknown",
            location=raw.get("location") or "Remote",
            remote=True,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="USD",
            job_type="full_time",
            level="mid",
            skills=[t for t in (raw.get("tags") or []) if isinstance(t, str)],
            description=strip_html(raw.get("description")),
            apply_url=raw.get("url") or raw.get("apply_url") or "",
            apply_on="Remote OK",
            posted_at=posted_at or datetime.now(timezone.utc),
            company_logo=raw.get("logo"),
        )


remoteok_provider = RemoteOKProvider()