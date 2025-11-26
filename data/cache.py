"""Simple in-memory cache helper for read-heavy lookups.

This module intentionally keeps the interface tiny so it can be easily
swapped or extended later without touching callers.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any, Hashable, Optional


class LRUCache:
    """A tiny LRU cache with a max size.

    This is process-local and not safe for multi-process sharing,
    which is acceptable for this educational project.
    """

    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._store: "OrderedDict[Hashable, Any]" = OrderedDict()

    def get(self, key: Hashable) -> Optional[Any]:
        if key not in self._store:
            return None
        # Mark as recently used
        value = self._store.pop(key)
        self._store[key] = value
        return value

    def set(self, key: Hashable, value: Any) -> None:
        if key in self._store:
            self._store.pop(key)
        elif len(self._store) >= self.maxsize:
            # evict least-recently-used
            self._store.popitem(last=False)
        self._store[key] = value

    def invalidate(self, key: Hashable) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# Singleton caches for common lookups
country_by_code_cache = LRUCache(maxsize=256)
state_by_code_cache = LRUCache(maxsize=512)
city_by_name_state_cache = LRUCache(maxsize=1024)
