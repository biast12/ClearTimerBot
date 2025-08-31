from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    NONE = "NONE"  # Special case - doesn't display level field


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class BotConfig:
    token: str
    owner_id: Optional[int] = None
    guild_id: Optional[int] = None
    application_id: Optional[str] = None
    database_url: Optional[str] = None
    prefix: str = "!"
    environment: Environment = Environment.PRODUCTION
    log_level: LogLevel = LogLevel.INFO
    shard_count: Optional[int] = None
    shard_ids: Optional[List[int]] = None
    
    @property
    def is_owner_mode(self) -> bool:
        return self.owner_id is not None and self.guild_id is not None
    
    @classmethod
    def from_env(cls, env_vars: Dict[str, str]) -> "BotConfig":
        return cls(
            token=env_vars["DISCORD_BOT_TOKEN"],
            owner_id=int(env_vars["OWNER_ID"]) if env_vars.get("OWNER_ID") else None,
            guild_id=int(env_vars["GUILD_ID"]) if env_vars.get("GUILD_ID") else None,
            application_id=env_vars.get("APPLICATION_ID"),
            database_url=env_vars.get("DATABASE_URL"),
            prefix=env_vars.get("BOT_PREFIX", "!"),
            environment=Environment(env_vars.get("ENVIRONMENT", "production")),
            log_level=LogLevel(env_vars.get("LOG_LEVEL", "INFO")),
            shard_count=int(env_vars["SHARD_COUNT"]) if "SHARD_COUNT" in env_vars else None,
            shard_ids=[int(x) for x in env_vars["SHARD_IDS"].split(",")] if "SHARD_IDS" in env_vars else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "owner_id": self.owner_id,
            "prefix": self.prefix,
            "environment": self.environment.value,
            "log_level": self.log_level.value,
            "shard_count": self.shard_count,
            "shard_ids": self.shard_ids
        }


@dataclass
class SchedulerConfig:
    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    retry_delay_seconds: int = 60
    cleanup_interval_seconds: int = 3600
    max_queue_size: int = 1000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout_seconds": self.task_timeout_seconds,
            "retry_delay_seconds": self.retry_delay_seconds,
            "cleanup_interval_seconds": self.cleanup_interval_seconds,
            "max_queue_size": self.max_queue_size
        }


@dataclass
class CacheConfig:
    memory_max_size: int = 1000
    memory_ttl_seconds: int = 300
    warm_max_size: int = 5000
    warm_ttl_seconds: int = 900
    cold_max_size: int = 10000
    cold_ttl_seconds: int = 3600
    eviction_policy: str = "lru"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_max_size": self.memory_max_size,
            "memory_ttl_seconds": self.memory_ttl_seconds,
            "warm_max_size": self.warm_max_size,
            "warm_ttl_seconds": self.warm_ttl_seconds,
            "cold_max_size": self.cold_max_size,
            "cold_ttl_seconds": self.cold_ttl_seconds,
            "eviction_policy": self.eviction_policy
        }


@dataclass
class RateLimitConfig:
    commands_per_minute: int = 30
    commands_per_hour: int = 500
    clear_operations_per_hour: int = 100
    api_calls_per_second: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "commands_per_minute": self.commands_per_minute,
            "commands_per_hour": self.commands_per_hour,
            "clear_operations_per_hour": self.clear_operations_per_hour,
            "api_calls_per_second": self.api_calls_per_second
        }


@dataclass
class FeatureFlags:
    enable_analytics: bool = True
    enable_caching: bool = True
    enable_auto_cleanup: bool = True
    enable_error_reporting: bool = True
    enable_performance_monitoring: bool = False
    enable_debug_commands: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_analytics": self.enable_analytics,
            "enable_caching": self.enable_caching,
            "enable_auto_cleanup": self.enable_auto_cleanup,
            "enable_error_reporting": self.enable_error_reporting,
            "enable_performance_monitoring": self.enable_performance_monitoring,
            "enable_debug_commands": self.enable_debug_commands
        }


@dataclass
class ApplicationConfig:
    bot: BotConfig
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    rate_limits: RateLimitConfig = field(default_factory=RateLimitConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bot": self.bot.to_dict(),
            "scheduler": self.scheduler.to_dict(),
            "cache": self.cache.to_dict(),
            "rate_limits": self.rate_limits.to_dict(),
            "features": self.features.to_dict()
        }