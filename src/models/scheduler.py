from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    channel_id: str
    guild_id: str
    scheduled_time: datetime
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def is_ready(self) -> bool:
        return (
            self.status == TaskStatus.PENDING
            and datetime.now(timezone.utc) >= self.scheduled_time
        )

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)

    def increment_retry(self) -> None:
        self.retry_count += 1
        self.status = TaskStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        scheduled_time = data.get("scheduled_time")
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(scheduled_time)

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        started_at = data.get("started_at")
        if started_at and isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = data.get("completed_at")
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            task_id=data["task_id"],
            name=data["name"],
            channel_id=data["channel_id"],
            guild_id=data["guild_id"],
            scheduled_time=scheduled_time,
            status=TaskStatus(data.get("status", "pending")),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )


@dataclass
class SchedulerStats:
    total_tasks_scheduled: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    total_tasks_cancelled: int = 0
    average_execution_time_seconds: float = 0.0
    current_queue_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks_scheduled": self.total_tasks_scheduled,
            "total_tasks_completed": self.total_tasks_completed,
            "total_tasks_failed": self.total_tasks_failed,
            "total_tasks_cancelled": self.total_tasks_cancelled,
            "average_execution_time_seconds": self.average_execution_time_seconds,
            "current_queue_size": self.current_queue_size,
            "success_rate": f"{(self.total_tasks_completed / max(self.total_tasks_scheduled, 1)) * 100:.2f}%",
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchedulerStats":
        return cls(
            total_tasks_scheduled=data.get("total_tasks_scheduled", 0),
            total_tasks_completed=data.get("total_tasks_completed", 0),
            total_tasks_failed=data.get("total_tasks_failed", 0),
            total_tasks_cancelled=data.get("total_tasks_cancelled", 0),
            average_execution_time_seconds=data.get(
                "average_execution_time_seconds", 0.0
            ),
            current_queue_size=data.get("current_queue_size", 0),
        )
