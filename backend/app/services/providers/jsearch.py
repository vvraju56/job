"""JSearch provider (multi-source job search, hosted by OpenWeb Ninja).

Endpoint: GET https://api.openwebninja.com/jsearch/search-v2
Auth: `X-API-Key` header (same key as the salary/autocomplete add-ons).
Response shape: `{"status": "OK", "data": {"jobs": [ {job...} ]}}`.
Pagination is cursor-based on this host; we request a single page
(`num_pages=1`) and let the aggregator cache the results.
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

API_URL = "https://api.openwebninja.com/jsearch/search-v2"
DETAIL_URL = "https://api.openwebninja.com/jsearch/job-details"

EMP_TYPE_MAP = {
    "fulltime": "full_time",
    "full_time": "full_time",
    "parttime": "part_time",
    "part_time": "part_time",
    "contract": "contract",
    "contractor": "contract",
    "intern": "internship",
    "internship": "internship",
}


class JSearchProvider(JobProvider):
    """JSearch / RapidAPI-style multi-source provider."""

    name = "jsearch"

    @property
    def configured(self) -> bool:
        return bool(settings.JSEARCH_API_KEY)

    async def search(
        self,
        query: str,
        location: str = DEFAULT_LOCATION,
        page: int = 1,
        filters: JobFilters | None = None,
    ) -> list[NormalizedJob]:
        if not self.configured:
            raise ProviderNotConfigured("JSEARCH_API_KEY is not configured.")
        filters = filters or {}
        params: dict[str, Any] = {"query": query, "num_pages": 1}
        if location and location.lower() not in {"india", "anywhere", "remote", "worldwide"}:
            params["location"] = location
        date_posted = filters.get("date_posted")
        if date_posted in {"today", "3days", "week", "month"}:
            params["date_posted"] = date_posted

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(API_URL, params=params, headers={"X-API-Key": settings.JSEARCH_API_KEY})
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403, 429):
                raise QuotaExceeded("JSearch API rejected the request") from exc
            raise QuotaExceeded(f"JSearch request failed: {exc}") from exc
        except httpx.HTTPError as exc:
            raise QuotaExceeded(f"JSearch request failed: {exc}") from exc

        if not isinstance(data, dict):
            return []
        if data.get("status") == "ERROR":
            raise QuotaExceeded(str((data.get("error") or {}).get("message") or "JSearch request failed"))
        raw = (data.get("data") or {}).get("jobs") if isinstance(data.get("data"), dict) else data.get("data")
        items = raw if isinstance(raw, list) else []
        return [self.normalize(item) for item in items]

    async def get_job(self, external_id: str, company: str | None = None) -> NormalizedJob | None:
        if not self.configured:
            return None
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    DETAIL_URL, params={"job_id": external_id}, headers={"X-API-Key": settings.JSEARCH_API_KEY}
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
        except httpx.HTTPError:
            return None

        if not isinstance(data, dict) or data.get("status") != "OK":
            return None
        items = data.get("data") or []
        if isinstance(items, list) and items:
            return self.normalize(items[0])
        return None

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        city = raw.get("job_city") or raw.get("city") or ""
        state = raw.get("job_state") or raw.get("state") or ""
        country = raw.get("job_country") or raw.get("country") or ""
        location = (
            raw.get("job_location")
            or raw.get("location")
            or ", ".join(p for p in (city, state) if p)
            or country
        )
        remote = bool(raw.get("job_is_remote") or raw.get("is_remote"))

        posted_raw = raw.get("job_posted_at_datetime_utc") or raw.get("posted_at")
        posted_at = None
        if posted_raw:
            try:
                posted_at = datetime.fromisoformat(str(posted_raw).replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        emp = (raw.get("job_employment_type") or raw.get("employment_type") or "").lower()
        return NormalizedJob(
            source=self.name,
            external_id=str(raw.get("job_id") or raw.get("id") or ""),
            title=raw.get("job_title") or raw.get("title") or "Untitled",
            company_name=raw.get("employer_name") or raw.get("company_name") or "Unknown",
            location=location,
            remote=remote,
            salary_min=raw.get("job_min_salary") or raw.get("min_salary"),
            salary_max=raw.get("job_max_salary") or raw.get("max_salary"),
            salary_currency=raw.get("job_salary_currency") or raw.get("salary_currency") or "USD",
            job_type=EMP_TYPE_MAP.get(emp, "full_time"),
            level="mid",
            skills=raw.get("job_required_skills") or raw.get("skills") or [],
            description=raw.get("job_description") or raw.get("description"),
            apply_url=raw.get("job_apply_link") or raw.get("apply_link") or "",
            apply_on="JSearch",
            posted_at=posted_at or datetime.now(timezone.utc),
            company_logo=raw.get("employer_logo") or raw.get("company_logo"),
        )


jsearch_provider = JSearchProvider()