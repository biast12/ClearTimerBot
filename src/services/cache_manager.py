from typing import Any, Dict, Optional, Set, List
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # TTL in seconds

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)


class CacheManager:
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._default_ttl = default_ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    self._stats["hits"] += 1
                    return entry.value
                else:
                    del self._cache[key]
                    self._stats["evictions"] += 1
            
            self._stats["misses"] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            ttl = ttl if ttl is not None else self._default_ttl
            self._cache[key] = CacheEntry(value=value, ttl=ttl)

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
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats["evictions"] += 1
            return len(expired_keys)

    def get_stats(self) -> Dict[str, int]:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        return {
            **self._stats,
            "total_requests": total,
            "hit_rate": round(hit_rate, 2),
            "cached_items": len(self._cache),
        }


class MultiLevelCache:
    def __init__(self):
        self.memory_cache = CacheManager(default_ttl=60)  # 1 minute for hot data
        self.warm_cache = CacheManager(default_ttl=300)  # 5 minutes for warm data
        self.cold_cache = CacheManager(default_ttl=3600)  # 1 hour for cold data

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

    async def set(self, key: str, value: Any, cache_level: str = "memory", ttl: Optional[int] = None) -> None:
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

    async def clear_all(self) -> None:
        await self.memory_cache.clear()
        await self.warm_cache.clear()
        await self.cold_cache.clear()

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        return {
            "memory": self.memory_cache.get_stats(),
            "warm": self.warm_cache.get_stats(),
            "cold": self.cold_cache.get_stats(),
        }