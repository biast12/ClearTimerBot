from typing import Any, Dict, Optional
import asyncio
from src.models import (
    CacheEntry as ModelCacheEntry,
    CacheLevel,
    CacheStats,
    GlobalCacheStats,
)
from src.config import get_global_config


class CacheManager:
    def __init__(
        self, level: CacheLevel, default_ttl: int = 300
    ):  # 5 minutes default TTL
        self._cache: Dict[str, ModelCacheEntry] = {}
        self._lock = asyncio.Lock()
        self._default_ttl = default_ttl
        self._level = level
        self._stats = CacheStats(level=level)

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    self._stats.total_hits += 1
                    entry.touch()
                    return entry.value
                else:
                    del self._cache[key]
                    self._stats.evictions += 1

            self._stats.total_misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            ttl = ttl if ttl is not None else self._default_ttl
            self._cache[key] = ModelCacheEntry(
                key=key, value=value, level=self._level, ttl=ttl
            )
            self._stats.total_entries = len(self._cache)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> int:
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats.evictions += 1
            self._stats.total_entries = len(self._cache)
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        self._stats.total_entries = len(self._cache)
        self._stats.calculate_hit_rate()
        return self._stats.to_dict()


class MultiLevelCache:
    def __init__(self):
        config = get_global_config()
        self.memory_cache = CacheManager(
            level=CacheLevel.MEMORY, default_ttl=config.default_cache_ttl_memory
        )
        self.warm_cache = CacheManager(
            level=CacheLevel.WARM, default_ttl=config.default_cache_ttl_warm
        )
        self.cold_cache = CacheManager(
            level=CacheLevel.COLD, default_ttl=config.default_cache_ttl_cold
        )
        self._global_stats = GlobalCacheStats()

    async def get(self, key: str, cache_level: str = "memory") -> Optional[Any]:
        if cache_level == "memory":
            value = await self.memory_cache.get(key)
            if value is not None:
                return value

            # Check warm cache
            value = await self.warm_cache.get(key)
            if value is not None:
                # Promote to memory cache
                await self.memory_cache.set(key, value)
                return value

            # Check cold cache
            value = await self.cold_cache.get(key)
            if value is not None:
                # Promote to warm cache
                await self.warm_cache.set(key, value)
                return value

        elif cache_level == "warm":
            return await self.warm_cache.get(key)
        elif cache_level == "cold":
            return await self.cold_cache.get(key)

        return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_level: str = "memory",
        ttl: Optional[int] = None,
    ) -> None:
        if cache_level == "memory":
            await self.memory_cache.set(key, value, ttl)
        elif cache_level == "warm":
            await self.warm_cache.set(key, value, ttl)
        elif cache_level == "cold":
            await self.cold_cache.set(key, value, ttl)

    async def invalidate(self, key: str) -> None:
        await self.memory_cache.delete(key)
        await self.warm_cache.delete(key)
        await self.cold_cache.delete(key)

    async def delete(self, key: str) -> None:
        """Alias for invalidate for consistency"""
        await self.invalidate(key)

    async def clear_all(self) -> None:
        await self.memory_cache.clear()
        await self.warm_cache.clear()
        await self.cold_cache.clear()

    def get_all_stats(self) -> Dict[str, Any]:
        self._global_stats.memory = self.memory_cache._stats
        self._global_stats.warm = self.warm_cache._stats
        self._global_stats.cold = self.cold_cache._stats
        return self._global_stats.get_total_stats()
