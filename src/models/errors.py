from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import traceback


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    DATABASE = "database"
    DISCORD_API = "discord_api"
    PERMISSION = "permission"
    VALIDATION = "validation"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    SCHEDULER = "scheduler"
    CACHE = "cache"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    user_id: Optional[str] = None
    command: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "user_id": self.user_id,
            "command": self.command,
            "additional_data": self.additional_data
        }


@dataclass
class ErrorRecord:
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception_type: str
    stack_trace: str
    context: ErrorContext
    resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    @classmethod
    def from_exception(
        cls,
        error_id: str,
        exception: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: ErrorContext
    ) -> "ErrorRecord":
        return cls(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            category=category,
            severity=severity,
            message=str(exception),
            exception_type=type(exception).__name__,
            stack_trace=traceback.format_exc(),
            context=context
        )
    
    def mark_resolved(self, notes: Optional[str] = None) -> None:
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        self.resolution_notes = notes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "exception_type": self.exception_type,
            "stack_trace": self.stack_trace,
            "context": self.context.to_dict(),
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class ErrorStats:
    total_errors: int = 0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    errors_by_severity: Dict[str, int] = field(default_factory=dict)
    resolved_errors: int = 0
    unresolved_errors: int = 0
    recent_errors: List[ErrorRecord] = field(default_factory=list)
    
    def add_error(self, error: ErrorRecord) -> None:
        self.total_errors += 1
        
        category_key = error.category.value
        self.errors_by_category[category_key] = self.errors_by_category.get(category_key, 0) + 1
        
        severity_key = error.severity.value
        self.errors_by_severity[severity_key] = self.errors_by_severity.get(severity_key, 0) + 1
        
        if error.resolved:
            self.resolved_errors += 1
        else:
            self.unresolved_errors += 1
        
        self.recent_errors.append(error)
        if len(self.recent_errors) > 100:
            self.recent_errors = self.recent_errors[-100:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_errors": self.total_errors,
            "errors_by_category": self.errors_by_category,
            "errors_by_severity": self.errors_by_severity,
            "resolved_errors": self.resolved_errors,
            "unresolved_errors": self.unresolved_errors,
            "recent_error_count": len(self.recent_errors)
        }


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    area: str
    message: str
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "area": self.area,
            "message": self.message,
            "context": self.context
        }


class LogArea(Enum):
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"
    DATABASE = "DATABASE"
    DISCORD = "DISCORD"
    COMMANDS = "COMMANDS"
    SCHEDULER = "SCHEDULER"
    CACHE = "CACHE"
    CLEANUP = "CLEANUP"
    ERROR = "ERROR"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    PERMISSIONS = "PERMISSIONS"
    GENERAL = "GENERAL"
    NONE = "NONE"  # Special case - doesn't display area field