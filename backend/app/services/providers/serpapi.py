"""SerpApi Google Jobs provider.

Wraps the SerpApi Google Jobs engine (https://serpapi.com/google-jobs-api).
All API key handling stays server-side — the key is never exposed to the
Next.js frontend or the Flutter app.

SerpApi free plan grants ~250 searches/month; every non-cached search is
tracked in `api_logs` so the Developer API Dashboard can monitor usage.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.adapters.base import NormalizedJob
from app.core.config import settings
from app.services.providers.base import (
    DEFAULT_LOCATION,
    JobFilters,
    JobProvider,
    ProviderNotConfigured,
    QuotaExceeded,
)

JOB_TYPE_MAP = {
    "fulltime": "full_time",
    "full-time": "full_time",
    "parttime": "part_time",
    "part-time": "part_time",
    "contract": "contract",
    "internship": "internship",
    "temporary": "contract",
}

# SerpApi `experience` param values
EXPERIENCE_MAP = {
    "entry": "entrylevel",
    "mid": "midlevel",
    "senior": "seniorlevel",
    "lead": "director",
    "executive": "director",
}

_SALARY_NUMBER = re.compile(r"(\d[\d,\.]*)")
_SALARY_CURRENCY = re.compile(r"(₹|\$|€|£|¥)")
_POSTED_AGO = re.compile(r"(?:(\d+)\s*(?:days?|hours?|weeks?|months?))\s*ago")


def _parse_posted_at(text: str | None) -> datetime | None:
    """Parse '2 days ago' / '5 hours ago' style strings into a datetime."""
    if not text:
        return None
    match = _POSTED_AGO.search(text.lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(1).lower()
    now = datetime.now(timezone.utc)
    if "hour" in unit:
        return now - timedelta(hours=amount)
    if "day" in unit:
        return now - timedelta(days=amount)
    if "week" in unit:
        return now - timedelta(weeks=amount)
    if "month" in unit:
        return now - timedelta(days=30 * amount)
    return None


def _parse_salary(text: str | None) -> tuple[float | None, float | None, str]:
    """Best-effort parse of '₹12L – ₹18L/yr' / '$90,000 - $110,000' salary text."""
    if not text:
        return None, None, "INR"
    currency = "INR" if "₹" in text else (_SALARY_CURRENCY.search(text) or [None]).group(0) if _SALARY_CURRENCY.search(text) else "USD"
    currency_map = {"₹": "INR", "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
    currency = currency_map.get(currency, "INR")

    numbers = _SALARY_NUMBER.findall(text.replace(",", ""))
    if not numbers:
        return None, None, currency
    parsed = [float(n) for n in numbers if n]
    low, high = parsed[0], parsed[-1]
    # Indian "12L" shorthand: 12L -> 1,200,000
    if "l" in text.lower() or "lpa" in text.lower():
        low = low * 100_000
        if len(parsed) > 1:
            high = high * 100_000
    if low > high:
        low, high = high, low
    return low, high, currency


def _pick_apply_link(job: dict[str, Any]) -> tuple[str, str]:
    """Choose the best apply URL from apply_options. Returns (url, label)."""
    options = job.get("apply_options") or []
    candidates: list[tuple[str, str]] = []
    for option in options:
        title = (option.get("title") or "").lower()
        link = option.get("link") or ""
        if not link:
            continue
        label = option.get("title") or "Original Website"
        score = 0
        if "company" in title or "website" in title or "career" in title or "apply" in title:
            score = 2
        elif "google" in title or "easy apply" in title:
            score = 1
        candidates.append((label, link, score))
    candidates.sort(key=lambda item: item[2], reverse=True)
    if candidates:
        label, url, _ = candidates[0]
        return url, label

    # Fallback: Google Jobs listing page (points back to the original portal).
    via = job.get("via") or "Original Website"
    return f"https://www.google.com/search?q={job.get('title', '').replace(' ', '+')}&ibp=htl;jobs", via


class SerpApiProvider(JobProvider):
    """Default job provider backed by SerpApi's Google Jobs engine."""

    name = "serpapi"

    @property
    def configured(self) -> bool:
        return bool(settings.SERPAPI_API_KEY)

    def _require_config(self) -> None:
        if not self.configured:
            raise ProviderNotConfigured(
                "SERPAPI_API_KEY is not configured on the server."
            )

    async def search(
        self,
        query: str,
        location: str = DEFAULT_LOCATION,
        page: int = 1,
        filters: JobFilters | None = None,
    ) -> list[NormalizedJob]:
        self._require_config()
        filters = filters or {}

        params: dict[str, Any] = {
            "engine": "google_jobs",
            "q": query,
            "hl": "en",
            "gl": settings.SERPAPI_GL,
            "api_key": settings.SERPAPI_API_KEY,
            "page": max(0, int(page) - 1),  # SerpApi pages are 0-based
        }

        # Google Jobs rejects remote-like free-text locations ("remote",
        # "anywhere") — fall back to the default geo instead of a 400.
        loc = (location or DEFAULT_LOCATION).strip()
        if loc.lower() in {"remote", "anywhere", "worldwide", "virtual"}:
            loc = DEFAULT_LOCATION
        params["location"] = loc

        job_type = filters.get("job_type")
        if job_type in JOB_TYPE_MAP:
            params["jt"] = JOB_TYPE_MAP[job_type]

        level = filters.get("level")
        if level in EXPERIENCE_MAP:
            params["experience"] = EXPERIENCE_MAP[level]

        salary_min = filters.get("salary_min")
        if salary_min:
            params["salary"] = int(salary_min)

        date_posted = filters.get("date_posted")
        if date_posted in {"today", "3days", "week", "month"}:
            params["date_posted"] = date_posted

        try:
            from serpapi import Client, HTTPError

            client = Client(api_key=settings.SERPAPI_API_KEY, timeout=20)
            results = await asyncio.to_thread(client.search, params)
            data = results.as_dict() if hasattr(results, "as_dict") else dict(results)
        except HTTPError as exc:
            if getattr(exc, "status_code", None) in (401, 403, 429):
                raise QuotaExceeded("SerpApi rejected the request") from exc
            raise QuotaExceeded(f"SerpApi request failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if (
                "forbidden" in message
                or "rate" in message
                or "too many" in message
                or "invalid key" in message
            ):
                raise QuotaExceeded("SerpApi search quota exceeded") from exc
            raise QuotaExceeded(f"SerpApi request failed: {exc}") from exc

        if isinstance(data, dict) and data.get("error"):
            # "Google hasn't returned any results for this query" is a 200-level
            # no-results signal, not a quota/credential problem.
            if "hasn't returned any results" in str(data["error"]).lower():
                return []
            raise QuotaExceeded(str(data["error"]))

        raw_jobs = data.get("jobs_results") or []
        jobs: list[NormalizedJob] = []
        for raw in raw_jobs:
            job = self.normalize(raw)
            remote = bool(filters.get("remote"))
            if remote and not job.remote:
                continue
            jobs.append(job)
        return jobs

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        detected = raw.get("detected_extensions") or {}
        extensions = raw.get("extensions") or []
        title = raw.get("title") or "Untitled"
        company = raw.get("company_name") or "Unknown Company"
        via = raw.get("via") or "Original Website"

        salary_text = (
            raw.get("salary")
            or detected.get("salary")
            or next((e for e in extensions if _SALARY_NUMBER.search(e)), None)
        )
        salary_min, salary_max, currency = _parse_salary(salary_text)

        schedule = (detected.get("schedule_type") or "").lower()
        job_type = JOB_TYPE_MAP.get(schedule, "full_time")

        apply_url, apply_label = _pick_apply_link(raw)
        remote = bool(detected.get("work_from_home") or any("work from home" in e.lower() for e in extensions))

        return NormalizedJob(
            source=self.name,
            external_id=str(raw.get("job_id") or ""),
            title=title,
            company_name=company,
            location=raw.get("location"),
            remote=remote,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            salary_text=salary_text,
            job_type=job_type,
            level="mid",
            skills=[],
            description=raw.get("description"),
            apply_url=apply_url,
            apply_on=apply_label or via,
            posted_at=_parse_posted_at(detected.get("posted_at")) or datetime.now(timezone.utc),
            company_logo=raw.get("thumbnail"),
        )


serpapi_provider = SerpApiProvider()