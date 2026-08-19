"""Redis-backed response cache with an in-process fallback.

SerpApi searches are cached for 6 hours so repeated identical searches only
consume SerpApi quota once. If Redis is unavailable the cache transparently
falls back to an in-memory TTL store (per worker), which is still useful for
dev and keeps the API healthy during Redis maintenance.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

try:
    import redis as redis_lib
except ImportError:  # pragma: no cover
    redis_lib = None  # type: ignore[assignment]

CACHE_PREFIX = "makeable:serp:"
TTL_SECONDS = int(settings.SERPAPI_CACHE_TTL_HOURS * 3600)


def cache_key(query: str, location: str, page: int, filters: dict[str, Any] | None) -> str:
    """Stable cache key for a search invocation."""
    payload = json.dumps(
        {"q": query.lower().strip(), "l": (location or "").lower().strip(), "p": page, "f": filters or {}},
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{CACHE_PREFIX}{digest}"


class MemoryTTLStore:
    """Simple thread-safe-ish TTL dict used when Redis is unavailable."""

    def __init__(self) -> None:
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = __import__("threading").Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires, value = item
            if expires < time.time():
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._store[key] = (time.time() + ttl, value)
            while len(self._store) > 10_000:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._store)


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    entries: int = 0
    backend: str = "memory"

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return round(self.hits / total * 100, 1)


class CacheService:
    """Uniform get/set/stats facade over Redis or the in-memory fallback."""

    def __init__(self) -> None:
        self._client = None
        self._memory = MemoryTTLStore()
        self._hits = 0
        self._misses = 0
        self.backend = "memory"
        if redis_lib is not None and settings.REDIS_URL:
            try:
                self._client = redis_lib.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=1,
                    socket_timeout=1,
                    decode_responses=True,
                )
                self._client.ping()
                self.backend = "redis"
            except Exception:  # noqa: BLE001
                self._client = None
                self.backend = "memory"

    async def get(self, key: str) -> Any | None:
        if self._client is not None:
            try:
                raw = self._client.get(key)
            except Exception:  # noqa: BLE001
                raw = None
            if raw is not None:
                self._hits += 1
                try:
                    return json.loads(raw)
                except (TypeError, json.JSONDecodeError):
                    return None
            self._misses += 1
            return None
        value = self._memory.get(key)
        if value is not None:
            self._hits += 1
            return value
        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = TTL_SECONDS) -> None:
        if self._client is not None:
            try:
                self._client.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception:  # noqa: BLE001
                pass
        self._memory.set(key, value, ttl)

    async def clear(self) -> None:
        if self._client is not None:
            try:
                keys = self._client.keys(f"{CACHE_PREFIX}*")
                if keys:
                    self._client.delete(*keys)
            except Exception:  # noqa: BLE001
                pass
        self._memory.clear()

    def stats(self) -> CacheStats:
        entries = 0
        if self._client is not None:
            try:
                entries = len(self._client.keys(f"{CACHE_PREFIX}*"))
            except Exception:  # noqa: BLE001
                entries = self._memory.size()
        else:
            entries = self._memory.size()
        return CacheStats(hits=self._hits, misses=self._misses, entries=entries, backend=self.backend)


cache_service = CacheService()