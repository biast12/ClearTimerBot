import pytz
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.job import Job

from src.models import ChannelTimer
from src.services.data_service import DataService
from src.utils.timer_parser import TimerParser
from src.utils.logger import logger, LogArea


class SchedulerService:
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.scheduler = AsyncIOScheduler()
        self.timer_parser = TimerParser(data_service.get_timezone)
        self._clear_callback: Optional[Callable] = None
        self._notify_callback: Optional[Callable] = None

    def set_clear_callback(self, callback: Callable) -> None:
        self._clear_callback = callback

    def set_notify_callback(self, callback: Callable) -> None:
        self._notify_callback = callback
    
    async def _cleanup_cache(self) -> None:
        """Cleanup expired cache entries from all cache levels"""
        cache = self.data_service._cache
        
        # Cleanup expired entries in all cache levels
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

    async def initialize_jobs(self, bot) -> None:
        servers = await self.data_service.get_all_servers()
        
        # Get current guild IDs the bot is in
        current_guild_ids = {str(guild.id) for guild in bot.guilds}

        for server_id, server in servers.items():
            # Skip servers the bot is not in
            if server_id not in current_guild_ids:
                continue
            
            for channel_id, channel_timer in server.channels.items():
                await self._schedule_job(
                    bot=bot,
                    server_id=server_id,
                    channel_id=channel_id,
                    channel_timer=channel_timer,
                )

        # Schedule daily cleanup job for servers removed over 30 days ago
        self.scheduler.add_job(
            self.data_service.cleanup_old_removed_servers,
            "cron",
            hour=3,  # Run at 3 AM UTC daily
            minute=0,
            id="cleanup_removed_servers",
            replace_existing=True,
        )
        
        # Schedule periodic cache cleanup (every 15 minutes)
        self.scheduler.add_job(
            self._cleanup_cache,
            "interval",
            minutes=15,
            id="cleanup_cache",
            replace_existing=True,
        )

    async def _schedule_job(
        self, bot, server_id: str, channel_id: str, channel_timer: ChannelTimer
    ) -> None:
        job_id = self._make_job_id(server_id, channel_id)

        # Check if job needs rescheduling due to missed execution
        if channel_timer.next_run_time < datetime.now(pytz.UTC):
            await self._handle_missed_job(bot, server_id, channel_id, channel_timer)
            return

        # Parse the timer to get the trigger
        try:
            trigger, _ = self.timer_parser.parse(channel_timer.timer)
        except Exception as e:
            logger.error(LogArea.SCHEDULER, f"Error parsing timer for job {job_id}: {e}")
            return

        # Get the channel object
        channel = bot.get_channel(int(channel_id))
        if not channel:
            logger.warning(LogArea.SCHEDULER, f"Channel {channel_id} not found for job {job_id}")
            return

        # Schedule the job
        self.scheduler.add_job(
            self._clear_callback,
            trigger,
            args=[channel],
            id=job_id,
            next_run_time=channel_timer.next_run_time,
            replace_existing=True,
        )

    async def _handle_missed_job(
        self, bot, server_id: str, channel_id: str, channel_timer: ChannelTimer
    ) -> None:
        job_id = self._make_job_id(server_id, channel_id)

        # Parse timer to get new next_run_time
        try:
            trigger, next_run_time = self.timer_parser.parse(channel_timer.timer)
        except Exception as e:
            logger.error(LogArea.SCHEDULER, f"Error parsing timer for missed job {job_id}: {e}")
            return

        # Update the stored next_run_time
        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            server.channels[channel_id].next_run_time = next_run_time
            await self.data_service.save_servers()

        # Notify about missed clear if callback is set
        channel = bot.get_channel(int(channel_id))
        if channel and self._notify_callback:
            await self._notify_callback(channel, job_id)

        # Schedule with new time
        if channel:
            self.scheduler.add_job(
                self._clear_callback,
                trigger,
                args=[channel],
                id=job_id,
                next_run_time=next_run_time,
                replace_existing=True,
            )

    def add_job(
        self,
        channel_id: str,
        server_id: str,
        trigger: BaseTrigger,
        channel,
        next_run_time: Optional[datetime] = None,
    ) -> str:
        job_id = self._make_job_id(server_id, channel_id)

        self.scheduler.add_job(
            self._clear_callback,
            trigger,
            args=[channel],
            id=job_id,
            next_run_time=next_run_time,
            replace_existing=True,
        )

        return job_id

    def remove_job(self, server_id: str, channel_id: str) -> bool:
        job_id = self._make_job_id(server_id, channel_id)

        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job by its job_id directly"""
        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False

    def get_job(self, server_id: str, channel_id: str) -> Optional[Job]:
        job_id = self._make_job_id(server_id, channel_id)
        return self.scheduler.get_job(job_id)

    def job_exists(self, server_id: str, channel_id: str) -> bool:
        return self.get_job(server_id, channel_id) is not None

    def get_next_run_time(self, server_id: str, channel_id: str) -> Optional[datetime]:
        job = self.get_job(server_id, channel_id)
        return job.next_run_time if job else None

    def get_all_jobs(self) -> Dict[str, Any]:
        jobs = {}
        for job in self.scheduler.get_jobs():
            jobs[job.id] = {
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            }
        return jobs

    @staticmethod
    def _make_job_id(server_id: str, channel_id: str) -> str:
        return f"{server_id}_{channel_id}"
