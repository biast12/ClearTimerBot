from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from enum import Enum
import traceback


class CollectionName(Enum):
    SERVERS = "servers"
    BLACKLIST = "blacklist"
    TIMEZONES = "timezones"
    REMOVED_SERVERS = "removed_servers"
    ERRORS = "errors"


@dataclass
class BlacklistEntry:
    server_id: str
    server_name: str = "Unknown"
    blacklisted_at: Optional[datetime] = None
    reason: Optional[str] = None

    def __post_init__(self):
        if self.blacklisted_at is None:
            self.blacklisted_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.server_id,
            "server_name": self.server_name,
            "blacklisted_at": self.blacklisted_at.isoformat() if self.blacklisted_at else None,
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlacklistEntry":
        blacklisted_at = data.get("blacklisted_at")
        if blacklisted_at and isinstance(blacklisted_at, str):
            blacklisted_at = datetime.fromisoformat(blacklisted_at)
        elif blacklisted_at is None:
            blacklisted_at = datetime.now(timezone.utc)
        
        return cls(
            server_id=str(data["_id"]),
            server_name=data.get("server_name", "Unknown"),
            blacklisted_at=blacklisted_at,
            reason=data.get("reason")
        )


@dataclass
class RemovedServer:
    server_id: str
    server_name: str
    removed_at: datetime
    channel_count: int = 0
    removal_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.server_id,
            "server_name": self.server_name,
            "removed_at": self.removed_at.isoformat() if isinstance(self.removed_at, datetime) else self.removed_at,
            "channel_count": self.channel_count,
            "removal_reason": self.removal_reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemovedServer":
        removed_at = data.get("removed_at")
        if isinstance(removed_at, str):
            removed_at = datetime.fromisoformat(removed_at)
        elif removed_at is None:
            removed_at = datetime.now(timezone.utc)
        
        if removed_at.tzinfo is None:
            removed_at = removed_at.replace(tzinfo=timezone.utc)
        
        return cls(
            server_id=str(data["_id"]),
            server_name=data.get("server_name", "Unknown"),
            removed_at=removed_at,
            channel_count=data.get("channel_count", 0),
            removal_reason=data.get("removal_reason")
        )


@dataclass
class TimezoneMapping:
    abbreviation: str
    full_name: str
    utc_offset: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        result = {self.abbreviation: self.full_name}
        if self.utc_offset:
            result[f"{self.abbreviation}_offset"] = self.utc_offset
        return result

    @classmethod
    def from_dict(cls, abbr: str, full_name: str, offset: Optional[str] = None) -> "TimezoneMapping":
        return cls(
            abbreviation=abbr,
            full_name=full_name,
            utc_offset=offset
        )


@dataclass 
class TimezoneDocument:
    timezones: Dict[str, str] = field(default_factory=dict)
    
    def add_timezone(self, abbreviation: str, full_name: str) -> None:
        self.timezones[abbreviation] = full_name
    
    def get_timezone(self, abbreviation: str) -> Optional[str]:
        return self.timezones.get(abbreviation)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.timezones
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimezoneDocument":
        tz_doc = cls()
        for key, value in data.items():
            if key != "_id":
                tz_doc.timezones[key] = value
        return tz_doc


@dataclass
class ErrorDocument:
    error_id: str
    timestamp: datetime
    level: str
    area: str
    message: str
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    user_id: Optional[str] = None
    command: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.error_id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "level": self.level,
            "area": self.area,
            "message": self.message,
            "exception_type": self.exception_type,
            "stack_trace": self.stack_trace,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "user_id": self.user_id,
            "command": self.command,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorDocument":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        resolved_at = data.get("resolved_at")
        if resolved_at and isinstance(resolved_at, str):
            resolved_at = datetime.fromisoformat(resolved_at)
        
        return cls(
            error_id=str(data.get("_id", data.get("error_id"))),
            timestamp=timestamp,
            level=data.get("level", "ERROR"),
            area=data.get("area", "UNKNOWN"),
            message=data.get("message", ""),
            exception_type=data.get("exception_type"),
            stack_trace=data.get("stack_trace"),
            guild_id=data.get("guild_id"),
            channel_id=data.get("channel_id"),
            user_id=data.get("user_id"),
            command=data.get("command"),
            resolved=data.get("resolved", False),
            resolved_at=resolved_at,
            resolution_notes=data.get("resolution_notes")
        )
    
    @classmethod
    def from_exception(
        cls,
        error_id: str,
        exception: Exception,
        level: str = "ERROR",
        area: str = "UNKNOWN",
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        command: Optional[str] = None
    ) -> "ErrorDocument":
        return cls(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            level=level,
            area=area,
            message=str(exception),
            exception_type=type(exception).__name__,
            stack_trace=traceback.format_exc(),
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            command=command
        )


@dataclass
class DatabaseStats:
    total_servers: int = 0
    total_channels: int = 0
    blacklisted_servers: int = 0
    removed_servers: int = 0
    active_timers: int = 0
    total_errors: int = 0
    unresolved_errors: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "total_servers": self.total_servers,
            "total_channels": self.total_channels,
            "blacklisted_servers": self.blacklisted_servers,
            "removed_servers": self.removed_servers,
            "active_timers": self.active_timers,
            "total_errors": self.total_errors,
            "unresolved_errors": self.unresolved_errors
        }