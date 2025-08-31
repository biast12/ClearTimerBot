from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    channel_id: str
    guild_id: str
    scheduled_time: datetime
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def is_ready(self) -> bool:
        return (
            self.status == TaskStatus.PENDING and 
            datetime.now(timezone.utc) >= self.scheduled_time
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
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


@dataclass
class ClearTask:
    channel_id: str
    guild_id: str
    scheduled_time: datetime
    timer_expression: str
    ignored_message_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "timer_expression": self.timer_expression,
            "ignored_message_ids": self.ignored_message_ids
        }


@dataclass
class TaskQueue:
    tasks: List[ScheduledTask] = field(default_factory=list)
    
    def add_task(self, task: ScheduledTask) -> None:
        self.tasks.append(task)
        self.tasks.sort(key=lambda t: (t.scheduled_time, -t.priority.value))
    
    def get_ready_tasks(self) -> List[ScheduledTask]:
        now = datetime.now(timezone.utc)
        return [
            task for task in self.tasks 
            if task.is_ready() and task.status == TaskStatus.PENDING
        ]
    
    def remove_completed(self) -> int:
        before_count = len(self.tasks)
        self.tasks = [
            task for task in self.tasks 
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
        ]
        return before_count - len(self.tasks)
    
    def get_stats(self) -> Dict[str, int]:
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for task in self.tasks:
            stats[task.status.value] += 1
        
        return stats


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
            "success_rate": f"{(self.total_tasks_completed / max(self.total_tasks_scheduled, 1)) * 100:.2f}%"
        }


from typing import List