"""Greenhouse ATS provider (company careers boards, keyless).

Greenhouse exposes public job boards per company slug:
GET https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true

Because boards are company-scoped (no keyword search), this provider only
participates when a `company` filter is supplied.
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

API_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
DETAIL_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"


class GreenhouseProvider(JobProvider):
    """Greenhouse ATS job board adapter."""

    name = "greenhouse"
    supports_query_search = False

    @property
    def configured(self) -> bool:
        return True  # public API, no key required

    async def search(
        self,
        query: str,
        location: str = DEFAULT_LOCATION,
        page: int = 1,
        filters: JobFilters | None = None,
    ) -> list[NormalizedJob]:
        filters = filters or {}
        company = filters.get("company") or (query.strip() if query.strip() else None)
        if not company:
            return []
        company_slug = company.strip().lower().replace(" ", "-")

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(API_URL.format(company=company_slug), params={"content": "true"})
                if resp.status_code == 404:
                    return []  # no such board
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return []

        jobs = data.get("jobs") or []
        jobs.sort(key=lambda j: j.get("updated_at") or "", reverse=True)
        return [self.normalize(job, company_slug) for job in jobs[:20]]

    async def get_job(self, external_id: str, company: str | None = None) -> NormalizedJob | None:
        if not company:
            return None
        company_slug = company.strip().lower().replace(" ", "-")
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(DETAIL_URL.format(company=company_slug, job_id=external_id))
                if resp.status_code != 200:
                    return None
                data = resp.json()
        except httpx.HTTPError:
            return None
        return self.normalize(data, company_slug)

    def normalize(self, raw: dict[str, Any], company_slug: str) -> NormalizedJob:
        metadata = {str(m.get("name", "")).lower(): str(m.get("value", "")) for m in raw.get("metadata") or []}
        remote = metadata.get("remote", "").lower() in {"yes", "true", "remote"}
        title = raw.get("title") or "Untitled"
        if not remote and "remote" in title.lower():
            remote = True

        emp = metadata.get("employment type", "").lower()
        if "part" in emp:
            job_type = "part_time"
        elif "contract" in emp or "temporary" in emp:
            job_type = "contract"
        elif "intern" in emp:
            job_type = "internship"
        else:
            job_type = "full_time"

        posted_raw = raw.get("updated_at")
        posted_at = None
        if posted_raw:
            try:
                posted_at = datetime.fromisoformat(str(posted_raw).replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        location = (raw.get("location") or {}).get("name")
        company = metadata.get("company") or company_slug.title()

        return NormalizedJob(
            source=self.name,
            external_id=str(raw.get("id") or ""),
            title=title,
            company_name=company,
            location=location,
            remote=remote,
            salary_min=None,
            salary_max=None,
            salary_currency="USD",
            job_type=job_type,
            level="mid",
            skills=raw.get("key_skills") or [],
            description=strip_html(raw.get("content")),
            apply_url=raw.get("absolute_url") or "",
            apply_on="Greenhouse",
            posted_at=posted_at or datetime.now(timezone.utc),
        )


greenhouse_provider = GreenhouseProvider()