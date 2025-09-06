import pytz
from datetime import datetime
from typing import Optional, Callable, Dict, Any, TYPE_CHECKING
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.job import Job

from src.models import (
    ChannelTimer,
    ScheduledTask,
    SchedulerStats
)
from src.services.server_data_service import DataService
from src.utils.schedule_parser import ScheduleExpressionParser
from src.utils.logger import logger, LogArea
from src.config import get_global_config

if TYPE_CHECKING:
    from src.core.bot import ClearTimerBot


class SchedulerService:
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.scheduler = AsyncIOScheduler()
        self.schedule_parser = ScheduleExpressionParser(
            data_service.get_timezone,
            data_service.get_timezone_for_server
        )
        self._clear_callback: Optional[Callable] = None
        self._notify_callback: Optional[Callable] = None
        self._stats = SchedulerStats()

    def register_channel_clear_callback(self, callback: Callable) -> None:
        self._clear_callback = callback

    def register_missed_clear_notification_callback(self, callback: Callable) -> None:
        self._notify_callback = callback
    
    async def _perform_periodic_cache_cleanup(self) -> None:
        cache = self.data_service._cache
        
        memory_cleaned = await cache.memory_cache.cleanup_expired()
        warm_cleaned = await cache.warm_cache.cleanup_expired()
        cold_cleaned = await cache.cold_cache.cleanup_expired()
        
        total_cleaned = memory_cleaned + warm_cleaned + cold_cleaned
        if total_cleaned > 0:
            logger.debug(LogArea.CACHE, f"Cache cleanup: Removed {total_cleaned} expired entries (Memory: {memory_cleaned}, Warm: {warm_cleaned}, Cold: {cold_cleaned})")

    async def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

    async def initialize_all_scheduled_jobs(self, bot) -> None:
        servers = await self.data_service.get_all_servers()
        
        current_guild_ids = {str(guild.id) for guild in bot.guilds}

        for server_id, server in servers.items():
            if server_id not in current_guild_ids:
                continue
            
            for channel_id, channel_timer in server.channels.items():
                await self._create_scheduled_clear_job(
                    bot=bot,
                    server_id=server_id,
                    channel_id=channel_id,
                    channel_timer=channel_timer,
                )

        self.scheduler.add_job(
            self.data_service.cleanup_old_removed_servers,
            "cron",
            hour=3,
            minute=0,
            id="cleanup_removed_servers",
            replace_existing=True,
        )
        
        config = get_global_config()
        self.scheduler.add_job(
            self._perform_periodic_cache_cleanup,
            "interval",
            seconds=config.cache_cleanup_interval,
            id="cleanup_cache",
            replace_existing=True,
        )

    async def _create_scheduled_clear_job(
        self, bot: "ClearTimerBot", server_id: str, channel_id: str, channel_timer: ChannelTimer
    ) -> None:
        job_id = self._create_job_identifier(server_id, channel_id)
        
        self._stats.total_tasks_scheduled += 1

        if channel_timer.next_run_time < datetime.now(pytz.UTC):
            await self._reschedule_missed_clear_job(bot, server_id, channel_id, channel_timer)
            return

        try:
            trigger, _ = self.schedule_parser.parse_schedule_expression(channel_timer.timer, server_id)
        except Exception as e:
            logger.error(LogArea.SCHEDULER, f"Error parsing timer for job {job_id}: {e}")
            return

        channel = bot.get_channel(int(channel_id))
        if not channel:
            logger.warning(LogArea.SCHEDULER, f"Channel {channel_id} not found for job {job_id}")
            return

        task = ScheduledTask(
            task_id=job_id,
            name=f"clear_{channel_id}",
            channel_id=channel_id,
            guild_id=server_id,
            scheduled_time=channel_timer.next_run_time
        )
        
        self.scheduler.add_job(
            self._clear_callback,
            trigger,
            args=[channel],
            id=job_id,
            next_run_time=channel_timer.next_run_time,
            replace_existing=True,
        )

    async def _reschedule_missed_clear_job(
        self, bot: "ClearTimerBot", server_id: str, channel_id: str, channel_timer: ChannelTimer
    ) -> None:
        job_id = self._create_job_identifier(server_id, channel_id)

        try:
            trigger, next_run_time = self.schedule_parser.parse_schedule_expression(channel_timer.timer, server_id)
        except Exception as e:
            logger.error(LogArea.SCHEDULER, f"Error parsing timer for missed job {job_id}: {e}")
            return

        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            server.channels[channel_id].next_run_time = next_run_time
            await self.data_service.save_servers()

        channel = bot.get_channel(int(channel_id))
        if channel and self._notify_callback:
            await self._notify_callback(channel, job_id)

        if channel:
            task = ScheduledTask(
                task_id=job_id,
                name=f"clear_{channel_id}",
                channel_id=channel_id,
                guild_id=server_id,
                scheduled_time=next_run_time
            )
            
            self.scheduler.add_job(
                self._clear_callback,
                trigger,
                args=[channel],
                id=job_id,
                next_run_time=next_run_time,
                replace_existing=True,
            )

    def create_channel_clear_job(
        self,
        channel_id: str,
        server_id: str,
        trigger: BaseTrigger,
        channel: discord.TextChannel,
        next_run_time: Optional[datetime] = None,
    ) -> str:
        job_id = self._create_job_identifier(server_id, channel_id)

        self.scheduler.add_job(
            self._clear_callback,
            trigger,
            args=[channel],
            id=job_id,
            next_run_time=next_run_time,
            replace_existing=True,
        )

        return job_id

    def remove_channel_clear_job(self, server_id: str, channel_id: str) -> bool:
        job_id = self._create_job_identifier(server_id, channel_id)

        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False
    
    async def cancel_job_by_id(self, job_id: str) -> bool:
        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False

    def get_channel_clear_job(self, server_id: str, channel_id: str) -> Optional[Job]:
        job_id = self._create_job_identifier(server_id, channel_id)
        return self.scheduler.get_job(job_id)

    def channel_has_active_job(self, server_id: str, channel_id: str) -> bool:
        return self.get_channel_clear_job(server_id, channel_id) is not None

    def get_channel_next_clear_time(self, server_id: str, channel_id: str) -> Optional[datetime]:
        job = self.get_channel_clear_job(server_id, channel_id)
        return job.next_run_time if job else None

    def get_all_scheduled_jobs(self) -> Dict[str, Any]:
        jobs = {}
        for job in self.scheduler.get_jobs():
            jobs[job.id] = {
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            }
        return jobs

    @staticmethod
    def _create_job_identifier(server_id: str, channel_id: str) -> str:
        return f"{server_id}_{channel_id}"
    
    def get_scheduler_statistics(self) -> Dict[str, Any]:
        self._stats.current_queue_size = len(self.scheduler.get_jobs())
        return self._stats.to_dict()
