from dataclasses import dataclass
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
            environment=Environment(env_vars.get("ENVIRONMENT", "production")),
            log_level=LogLevel(env_vars.get("LOG_LEVEL", "INFO")),
            shard_count=int(env_vars["SHARD_COUNT"]) if "SHARD_COUNT" in env_vars else None,
            shard_ids=[int(x) for x in env_vars["SHARD_IDS"].split(",")] if "SHARD_IDS" in env_vars else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "owner_id": self.owner_id,
            "environment": self.environment.value,
            "log_level": self.log_level.value,
            "shard_count": self.shard_count,
            "shard_ids": self.shard_ids
        }