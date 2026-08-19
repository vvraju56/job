"""OpenWebNinja add-on APIs that share the JSearch API key.

Two auxiliary endpoints on the same OpenWebNinja host accept the same
`X-API-Key` as the JSearch job search:

- Job salary data:      GET /job-salary-data/job-salary
- Web search autocomplete: GET /web-search-autocomplete/autocomplete

Both are cached with the standard search TTL so repeated calls are cheap and
never hammer the upstream. `configured` requires `JSEARCH_API_KEY`.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx

from app.core.config import settings
from app.services.cache import CACHE_PREFIX, cache_service
from app.services.providers.base import ProviderNotConfigured

SALARY_URL = "https://api.openwebninja.com/job-salary-data/job-salary"
AUTOCOMPLETE_URL = "https://api.openwebninja.com/web-search-autocomplete/autocomplete"

ADDON_PREFIX = CACHE_PREFIX + "addon:"


def _key(kind: str, params: dict[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{ADDON_PREFIX}{kind}:{digest}"


async def _get(url: str, params: dict[str, Any]) -> Any:
    if not settings.JSEARCH_API_KEY:
        raise ProviderNotConfigured("JSEARCH_API_KEY is not configured.")
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params, headers={"X-API-Key": settings.JSEARCH_API_KEY})
        resp.raise_for_status()
        return resp.json()


async def job_salary(job_title: str, location: str = "") -> tuple[Any, bool]:
    """Return (payload, cached) for the salary-data endpoint."""
    params: dict[str, Any] = {"job_title": job_title}
    if location:
        params["location"] = location
    key = _key("salary", params)
    cached = await cache_service.get(key)
    if cached is not None:
        return cached, True
    data = await _get(SALARY_URL, params)
    await cache_service.set(key, data)
    return data, False


async def autocomplete(query: str) -> tuple[Any, bool]:
    """Return (payload, cached) for the web-search autocomplete endpoint."""
    params: dict[str, Any] = {"query": query}
    key = _key("autocomplete", params)
    cached = await cache_service.get(key)
    if cached is not None:
        return cached, True
    data = await _get(AUTOCOMPLETE_URL, params)
    await cache_service.set(key, data)
    return data, False