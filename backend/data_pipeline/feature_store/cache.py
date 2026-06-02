"""
In-process feature cache.
Avoids re-fetching CSV/Understat data on every prediction call.
TTL-based: entries expire after `ttl_seconds` (default 6 hours).
"""
import time
from typing import Any
from dataclasses import dataclass, field


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float


class FeatureCache:
    def __init__(self, ttl_seconds: int = 21_600):  # 6 hours
        self._ttl = ttl_seconds
        self._store: dict[str, _CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = _CacheEntry(
            value=value,
            expires_at=time.monotonic() + self._ttl,
        )

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


# Module-level singleton used by feature_builder and predictor
feature_cache = FeatureCache()
