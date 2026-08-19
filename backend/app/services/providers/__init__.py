"""Provider registry.

New upstreams (LinkedIn partner API, Indeed official integrations, etc.)
implement `JobProvider` and are added to `PROVIDERS` here. `get_enabled_providers`
returns the providers selected by the `ENABLED_PROVIDERS` setting (the ones the
aggregator fans out to); the active single provider is selected via `JOB_PROVIDER`.
"""
from __future__ import annotations

from app.core.config import settings
from app.services.providers.base import JobProvider
from app.services.providers.serpapi import serpapi_provider
from app.services.providers.usajobs import usajobs_provider
from app.services.providers.jsearch import jsearch_provider
from app.services.providers.greenhouse import greenhouse_provider
from app.services.providers.ashby import ashby_provider
from app.services.providers.remoteok import remoteok_provider

PROVIDERS: dict[str, JobProvider] = {
    serpapi_provider.name: serpapi_provider,
    usajobs_provider.name: usajobs_provider,
    jsearch_provider.name: jsearch_provider,
    greenhouse_provider.name: greenhouse_provider,
    ashby_provider.name: ashby_provider,
    remoteok_provider.name: remoteok_provider,
}

# Deduplication priority when the same posting appears on several sources.
# Lower index wins.
SEARCH_PRIORITY = ["serpapi", "jsearch", "greenhouse", "ashby", "usajobs", "remoteok"]


def get_provider(name: str | None = None) -> JobProvider:
    """Return the named provider, falling back to the configured default."""
    provider = PROVIDERS.get(name or settings.JOB_PROVIDER)
    if provider is None:
        raise KeyError(f"Unknown job provider: {name or settings.JOB_PROVIDER}")
    return provider


def get_enabled_providers() -> list[JobProvider]:
    """Providers the aggregator queries for a search, in priority order."""
    names = settings.enabled_provider_list or [settings.JOB_PROVIDER]
    result: list[JobProvider] = []
    for name in names:
        provider = PROVIDERS.get(name)
        if provider is not None and provider not in result:
            result.append(provider)
    return result