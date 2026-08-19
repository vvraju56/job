"""USAJobs.gov open-data API provider (federal government jobs).

Docs: https://developer.usajobs.gov/
Endpoint: GET https://data.usajobs.gov/api/Search
Auth: `Authorization-Key` header + a `User-Agent` that must contain your email.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.adapters.base import NormalizedJob
from app.core.config import settings
from app.services.providers.base import (
    DEFAULT_LOCATION,
    JobFilters,
    JobProvider,
    ProviderNotConfigured,
    QuotaExceeded,
)

API_URL = "https://data.usajobs.gov/api/Search"

SCHEDULE_MAP = {
    "full-time": "full_time",
    "part-time": "part_time",
    "intermittent": "contract",
    "shift": "contract",
    "multiple schedules": "contract",
    "term": "contract",
    "temporary": "contract",
}


def _job_type(item: dict[str, Any]) -> str:
    schedules = item.get("PositionSchedule") or []
    for s in schedules:
        key = (s.get("Schedule") or "").lower()
        if key in SCHEDULE_MAP:
            return SCHEDULE_MAP[key]
    offerings = item.get("PositionOfferingType") or []
    for o in offerings:
        name = (o.get("Name") or "").lower()
        if "part" in name:
            return "part_time"
        if "full" in name:
            return "full_time"
        if "term" in name or "temporary" in name:
            return "contract"
        if "student" in name or "intern" in name:
            return "internship"
    return "full_time"


class USAJobsProvider(JobProvider):
    """Federal job listings from the USAJobs open-data API."""

    name = "usajobs"

    @property
    def configured(self) -> bool:
        return bool(settings.USAJOBS_API_KEY and settings.USAJOBS_EMAIL)

    async def search(
        self,
        query: str,
        location: str = DEFAULT_LOCATION,
        page: int = 1,
        filters: JobFilters | None = None,
    ) -> list[NormalizedJob]:
        if not self.configured:
            raise ProviderNotConfigured(
                "USAJOBS_API_KEY and USAJOBS_EMAIL are not configured."
            )
        params: dict[str, Any] = {
            "Keyword": query,
            "ResultsPerPage": 20,
            "Page": max(1, page),
        }
        if location and location.lower() not in {"india", "anywhere", "remote", "worldwide"}:
            params["LocationName"] = location

        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": settings.USAJOBS_EMAIL,
            "Authorization-Key": settings.USAJOBS_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(API_URL, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403, 429):
                raise QuotaExceeded("USAJobs API rejected the request") from exc
            raise QuotaExceeded(f"USAJobs request failed: {exc}") from exc
        except httpx.HTTPError as exc:
            raise QuotaExceeded(f"USAJobs request failed: {exc}") from exc

        items = (data.get("SearchResult") or {}).get("SearchResultItems") or []
        return [self.normalize(item) for item in items]

    async def get_job(self, external_id: str, company: str | None = None) -> NormalizedJob | None:
        if not self.configured:
            return None
        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": settings.USAJOBS_EMAIL,
            "Authorization-Key": settings.USAJOBS_API_KEY,
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    API_URL, params={"PositionID": external_id, "ResultsPerPage": 1}, headers=headers
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
        except httpx.HTTPError:
            return None

        items = (data.get("SearchResult") or {}).get("SearchResultItems") or []
        if not items:
            return None
        return self.normalize(items[0])

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        item = raw.get("MatchedObjectDescriptor") or raw
        locations = item.get("PositionLocation") or []
        location = locations[0].get("LocationName") if locations else None
        remote = bool(item.get("IsRemote")) or (location and "remote" in str(location).lower())

        salaries = item.get("PositionSalary") or []
        salary = salaries[0] if salaries else {}
        salary_min = float(salary.get("MinimumRange")) if salary.get("MinimumRange") else None
        salary_max = float(salary.get("MaximumRange")) if salary.get("MaximumRange") else None

        schedules = item.get("PositionSchedule") or []
        schedule = schedules[0].get("Schedule") if schedules else None

        descriptions = []
        for key in ("JobSummary", "QualificationSummary"):
            value = item.get(key)
            if value:
                descriptions.append(str(value).strip())
        description = "\n\n".join(descriptions) or None

        posted_raw = item.get("PublicationStartDate")
        posted_at = None
        if posted_raw:
            try:
                posted_at = datetime.fromisoformat(str(posted_raw).replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        apply_uris = item.get("ApplyURI") or []
        if isinstance(apply_uris, list):
            apply_url = apply_uris[0] if apply_uris else ""
        else:
            apply_url = apply_uris or ""

        return NormalizedJob(
            source=self.name,
            external_id=str(item.get("PositionID") or ""),
            title=item.get("PositionTitle") or "Untitled",
            company_name=item.get("OrganizationName") or "US Government",
            location=location,
            remote=remote,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="USD",
            job_type=_job_type(item),
            level="mid",
            skills=[],
            description=description,
            apply_url=apply_url,
            apply_on="USAJobs",
            posted_at=posted_at or datetime.now(timezone.utc),
            salary_text=(f"${salary_min:,.0f}–${salary_max:,.0f}" if salary_min and salary_max else None),
        )


usajobs_provider = USAJobsProvider()