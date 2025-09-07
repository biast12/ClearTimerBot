from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Dict
from enum import Enum


class CacheLevel(Enum):
    MEMORY = "memory"
    WARM = "warm"
    COLD = "cold"


@dataclass
class CacheEntry:
    key: str
    value: Any
    level: CacheLevel
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: Optional[int] = None
    access_count: int = 0

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        age = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return age > self.ttl

    def touch(self) -> None:
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "level": self.level.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "ttl": self.ttl,
            "access_count": self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)
        
        last_accessed = data.get("last_accessed")
        if isinstance(last_accessed, str):
            last_accessed = datetime.fromisoformat(last_accessed)
        elif last_accessed is None:
            last_accessed = datetime.now(timezone.utc)
        
        return cls(
            key=data["key"],
            value=data.get("value"),
            level=CacheLevel(data.get("level", "memory")),
            created_at=created_at,
            last_accessed=last_accessed,
            ttl=data.get("ttl"),
            access_count=data.get("access_count", 0)
        )


@dataclass
class CacheStats:
    level: CacheLevel
    total_entries: int = 0
    total_hits: int = 0
    total_misses: int = 0
    hit_rate: float = 0.0
    memory_usage_bytes: int = 0
    evictions: int = 0
    
    def calculate_hit_rate(self) -> None:
        total_requests = self.total_hits + self.total_misses
        if total_requests > 0:
            self.hit_rate = (self.total_hits / total_requests) * 100
        else:
            self.hit_rate = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "total_entries": self.total_entries,
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "hit_rate": f"{self.hit_rate:.2f}%",
            "memory_usage_bytes": self.memory_usage_bytes,
            "evictions": self.evictions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheStats":
        stats = cls(
            level=CacheLevel(data.get("level", "memory")),
            total_entries=data.get("total_entries", 0),
            total_hits=data.get("total_hits", 0),
            total_misses=data.get("total_misses", 0),
            memory_usage_bytes=data.get("memory_usage_bytes", 0),
            evictions=data.get("evictions", 0)
        )
        # Parse hit_rate if it's a string percentage
        hit_rate = data.get("hit_rate", "0.0%")
        if isinstance(hit_rate, str) and hit_rate.endswith("%"):
            stats.hit_rate = float(hit_rate[:-1])
        else:
            stats.calculate_hit_rate()
        return stats


@dataclass
class GlobalCacheStats:
    memory: CacheStats = field(default_factory=lambda: CacheStats(CacheLevel.MEMORY))
    warm: CacheStats = field(default_factory=lambda: CacheStats(CacheLevel.WARM))
    cold: CacheStats = field(default_factory=lambda: CacheStats(CacheLevel.COLD))
    
    def get_total_stats(self) -> Dict[str, Any]:
        total_hits = self.memory.total_hits + self.warm.total_hits + self.cold.total_hits
        total_misses = self.memory.total_misses + self.warm.total_misses + self.cold.total_misses
        total_entries = self.memory.total_entries + self.warm.total_entries + self.cold.total_entries
        total_memory = self.memory.memory_usage_bytes + self.warm.memory_usage_bytes + self.cold.memory_usage_bytes
        
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "total_entries": total_entries,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": f"{overall_hit_rate:.2f}%",
            "total_memory_usage_bytes": total_memory,
            "levels": {
                "memory": self.memory.to_dict(),
                "warm": self.warm.to_dict(),
                "cold": self.cold.to_dict()
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory": self.memory.to_dict(),
            "warm": self.warm.to_dict(),
            "cold": self.cold.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlobalCacheStats":
        return cls(
            memory=CacheStats.from_dict(data.get("memory", {"level": "memory"})) if "memory" in data else CacheStats(CacheLevel.MEMORY),
            warm=CacheStats.from_dict(data.get("warm", {"level": "warm"})) if "warm" in data else CacheStats(CacheLevel.WARM),
            cold=CacheStats.from_dict(data.get("cold", {"level": "cold"})) if "cold" in data else CacheStats(CacheLevel.COLD)
        )