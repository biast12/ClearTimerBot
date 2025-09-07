import asyncio
import pytz
from datetime import timedelta, datetime
from typing import Tuple, Set, Optional
import discord

from src.services.server_data_service import DataService
from src.services.clear_job_scheduler_service import SchedulerService
from src.utils.logger import logger, LogArea
from src.config import get_global_config


class MessageService:
    def __init__(self, data_service: DataService, scheduler_service: SchedulerService):
        self.data_service = data_service
        self.scheduler_service = scheduler_service
        self.rate_limit_delay = 1.0  # Delay between message deletions
        self.bot = None  # Will be set by the bot during initialization

    def set_bot(self, bot):
        """Set the bot instance after initialization"""
        self.bot = bot

    async def execute_channel_message_clear(self, channel: discord.TextChannel) -> None:
        if not await self._validate_bot_channel_permissions(channel):
            return

        ignored_messages, ignored_users = await self._get_ignored_entities(channel)

        server_id = str(channel.guild.id)
        channel_id = str(channel.id)
        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            view_message_id = server.channels[channel_id].view_message_id
            if view_message_id:
                ignored_messages.add(view_message_id)

        deleted_count = await self._perform_message_deletion(
            channel, ignored_messages, ignored_users
        )

        await self._update_next_scheduled_clear_time(channel)

    async def _get_ignored_entities(
        self, channel: discord.TextChannel
    ) -> Tuple[Set[str], Set[str]]:
        server_id = str(channel.guild.id)
        channel_id = str(channel.id)

        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            channel_timer = server.channels[channel_id]
            ignored_messages = set(channel_timer.ignored.messages)
            ignored_users = set(channel_timer.ignored.users)
            return ignored_messages, ignored_users
        return set(), set()

    async def _validate_bot_channel_permissions(
        self, channel: discord.TextChannel
    ) -> bool:
        cache_key = f"perms:{channel.guild.id}:{channel.id}:{channel.guild.me.id}"
        cached_result = await self.data_service._cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        permissions = channel.permissions_for(channel.guild.me)

        required_perms = {
            "view_channel": permissions.view_channel,
            "send_messages": permissions.send_messages,
            "read_message_history": permissions.read_message_history,
            "manage_messages": permissions.manage_messages,
            "embed_links": permissions.embed_links,
            "use_application_commands": permissions.use_application_commands,
            "send_messages_in_threads": permissions.send_messages_in_threads,
        }

        missing_perms = [
            perm for perm, has_perm in required_perms.items() if not has_perm
        ]

        result = len(missing_perms) == 0

        await self.data_service._cache.set(
            cache_key, result, cache_level="memory", ttl=900
        )

        if missing_perms:
            return False

        return True

    async def _perform_message_deletion(
        self,
        channel: discord.TextChannel,
        ignored_messages: Optional[Set[str]] = None,
        ignored_users: Optional[Set[str]] = None,
    ) -> int:
        deleted_count = 0
        ignored_messages = ignored_messages or set()
        ignored_users = ignored_users or set()

        try:
            two_weeks_ago = discord.utils.utcnow() - timedelta(days=13)

            messages_to_delete = []
            old_messages = []

            try:
                batch_size = 1000
                last_message = None

                while True:
                    messages_batch = []
                    async for message in channel.history(
                        limit=batch_size, before=last_message
                    ):
                        messages_batch.append(message)

                    if not messages_batch:
                        break

                    for message in messages_batch:
                        if str(message.id) in ignored_messages:
                            continue

                        if str(message.author.id) in ignored_users:
                            continue

                        if message.created_at > two_weeks_ago:
                            messages_to_delete.append(message)
                        else:
                            old_messages.append(message)

                    if len(messages_batch) < batch_size:
                        break

                    last_message = messages_batch[-1]
            except discord.Forbidden:
                logger.warning(
                    LogArea.PERMISSIONS,
                    f"No permission to access channel history for channel {channel.id}",
                )
                return 0

            if messages_to_delete:
                for i in range(0, len(messages_to_delete), 100):
                    batch = messages_to_delete[i : i + 100]
                    try:
                        await channel.delete_messages(batch)
                        deleted_count += len(batch)
                    except discord.HTTPException as e:
                        logger.warning(
                            LogArea.DISCORD,
                            f"Bulk delete failed: {e}, falling back to individual deletion",
                        )
                        for msg in batch:
                            try:
                                await msg.delete()
                                deleted_count += 1
                                await asyncio.sleep(self.rate_limit_delay)
                            except discord.HTTPException:
                                pass

            for message in old_messages:
                try:
                    await message.delete()
                    deleted_count += 1
                    await asyncio.sleep(self.rate_limit_delay)
                except discord.HTTPException:
                    pass

        except Exception as e:
            error_id = await logger.log_error(
                LogArea.SCHEDULER,
                f"Error clearing messages in channel {channel.id}",
                exception=e,
                channel_id=str(channel.id),
            )
            logger.error(
                LogArea.SCHEDULER,
                f"Error clearing messages in channel {channel.id}. Error ID: {error_id}",
            )

        return deleted_count

    async def _update_next_scheduled_clear_time(
        self, channel: discord.TextChannel
    ) -> None:
        server_id = str(channel.guild.id)
        channel_id = str(channel.id)

        next_run_time = self.scheduler_service.get_channel_next_clear_time(
            server_id, channel_id
        )

        if not next_run_time:
            return

        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            channel_timer = server.channels[channel_id]
            channel_timer.next_run_time = next_run_time.astimezone(pytz.UTC)

            if channel_timer.view_message_id:
                await self._update_view_message(
                    channel,
                    channel_timer.view_message_id,
                    channel_timer.timer,
                    next_run_time,
                )

            await self.data_service.save_servers()

    async def _update_view_message(
        self,
        channel: discord.TextChannel,
        message_id: str,
        timer: str,
        next_run_time: datetime,
    ) -> None:
        try:
            cache_key = f"discord:msg:{channel.id}:{message_id}"
            message = await self.data_service._cache.get(cache_key)

            if not message:
                message = await channel.fetch_message(int(message_id))
                await self.data_service._cache.set(
                    cache_key, message, cache_level="warm", ttl=3600
                )
            from src.components.subscription import TimerViewMessage
            from src.localization import get_translator

            server_id = str(channel.guild.id)
            translator = await get_translator(server_id, self.data_service)
            view = TimerViewMessage(channel, timer, next_run_time, translator)
            await message.edit(view=view)
        except discord.NotFound:
            server_id = str(channel.guild.id)
            channel_id = str(channel.id)
            server = await self.data_service.get_server(server_id)
            if server and channel_id in server.channels:
                server.channels[channel_id].view_message_id = None
                await self.data_service.save_servers()
        except Exception as e:
            logger.warning(LogArea.DISCORD, f"Failed to update view message: {e}")

    async def send_missed_clear_notification(
        self, channel: discord.TextChannel, job_id: str
    ) -> None:
        from src.components.errors import MissedClearView
        from src.localization import get_translator

        config = get_global_config()
        server_id = str(channel.guild.id)
        translator = await get_translator(server_id, self.data_service)

        # Create the view with notification message and Clear Now button
        view = MissedClearView(translator, channel, self, self.bot)

        await channel.send(
            view=view, delete_after=config.missed_clear_notification_timeout
        )
