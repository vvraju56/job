"""Job provider adapter contract.

Makeable Jobs uses a Provider Adapter Pattern: each upstream job source
(SerpApi Google Jobs, LinkedIn partner APIs, Indeed official integrations,
Greenhouse, Lever, Ashby, Workday, BambooHR, SmartRecruiters...) implements
the same `JobProvider` interface and returns normalized records. The default
provider is SerpApi; additional providers can be registered later without
changing the API surface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.adapters.base import NormalizedJob

JobFilters = dict[str, Any]

DEFAULT_LOCATION = "India"
DEFAULT_PAGE_SIZE = 20


def strip_html(text: str | None) -> str | None:
    """Remove HTML tags from ATS descriptions, collapsing whitespace."""
    if not text:
        return None
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "html.parser")
        cleaned = soup.get_text(" ")
    except Exception:  # noqa: BLE001
        import re

        cleaned = re.sub(r"<[^>]+>", " ", text)
    words = cleaned.split()
    return " ".join(words) or None


class ProviderError(Exception):
    """Base class for upstream provider failures."""


class QuotaExceeded(ProviderError):
    """Raised when the provider's search quota / rate limit is exhausted."""


class ProviderNotConfigured(ProviderError):
    """Raised when the provider has no API key configured."""


class JobProvider(ABC):
    """Interface every job source adapter must implement."""

    name: str = "base"

    @property
    @abstractmethod
    def configured(self) -> bool:
        """Whether this provider has credentials configured."""

    #: Whether this provider answers keyword searches (query + location).
    #: Company-board providers (Greenhouse, Ashby) set this False and are only
    #: queried when a company filter is supplied.
    supports_query_search: bool = True

    @abstractmethod
    async def search(
        self,
        query: str,
        location: str = DEFAULT_LOCATION,
        page: int = 1,
        filters: JobFilters | None = None,
    ) -> list[NormalizedJob]:
        """Search jobs and return normalized records.

        Args:
            query: Free-text job search (title, skill, company).
            location: Location to scope the search to.
            page: 1-based page number.
            filters: Optional provider-agnostic filters. Supported keys:
                remote (bool), salary_min (float), job_type (str),
                level (str), experience (int), date_posted (str).
        """
        raise NotImplementedError

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        """Default no-op; concrete providers implement field mapping."""
        raise NotImplementedError

    async def get_job(
        self,
        external_id: str,
        company: str | None = None,
    ) -> NormalizedJob | None:
        """Fetch a single job's full details live from the provider.

        Used by the auto-details flow so a job that is not persisted locally
        can still be rendered. Providers without a by-id lookup return None
        (the caller falls back to the relational DB).
        """
        return None