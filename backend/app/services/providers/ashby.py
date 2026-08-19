"""Ashby ATS provider (startup careers boards, keyless).

Ashby exposes public job boards through a GraphQL endpoint. Like Greenhouse,
boards are company-scoped, so this provider only participates when a `company`
filter is supplied. The request body mirrors Ashby's public non-user GraphQL
operation (`ApiJobBoardWithTeams`).
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

API_URL = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"

QUERY = """query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
  jobBoardWithTeams(organizationHostedJobsPageName: $organizationHostedJobsPageName) {
    jobPostings {
      id title locationName employmentType
      secondaryLocations { locationName }
    }
  }
}"""


class AshbyProvider(JobProvider):
    """Ashby ATS job board adapter."""

    name = "ashby"
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

        payload = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {"organizationHostedJobsPageName": company.strip().lower().replace(" ", "-")},
            "query": QUERY,
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(API_URL, json=payload)
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return []

        board = (data.get("data") or {}).get("jobBoardWithTeams") or {}
        postings = board.get("jobPostings") or []
        return [self.normalize(job, company) for job in postings[:20]]

    def normalize(self, raw: dict[str, Any], company: str) -> NormalizedJob:
        emp = (raw.get("employmentType") or "").lower()
        if "part" in emp:
            job_type = "part_time"
        elif "contract" in emp:
            job_type = "contract"
        elif "intern" in emp:
            job_type = "internship"
        else:
            job_type = "full_time"

        locations = [raw.get("locationName")]
        locations += [sec.get("locationName") for sec in raw.get("secondaryLocations") or []]
        locations = [loc for loc in locations if loc]

        job_id = str(raw.get("id") or "")
        return NormalizedJob(
            source=self.name,
            external_id=job_id,
            title=raw.get("title") or "Untitled",
            company_name=company.strip().title() or "Unknown",
            location=", ".join(locations) or None,
            remote=any("remote" in str(loc).lower() for loc in locations),
            salary_min=None,
            salary_max=None,
            salary_currency="USD",
            job_type=job_type,
            level="mid",
            skills=[],
            description=None,
            apply_url=f"https://jobs.ashbyhq.com/{company.strip().lower().replace(' ', '-')}/{job_id}"
            if job_id
            else "",
            apply_on="Ashby",
            posted_at=datetime.now(timezone.utc),
        )


ashby_provider = AshbyProvider()