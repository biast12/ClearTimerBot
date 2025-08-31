import asyncio
import pytz
from datetime import timedelta
import discord

from src.services.data_service import DataService
from src.services.scheduler_service import SchedulerService
from src.utils.logger import logger, LogArea


class MessageService:
    def __init__(self, data_service: DataService, scheduler_service: SchedulerService):
        self.data_service = data_service
        self.scheduler_service = scheduler_service
        self.rate_limit_delay = 1.0  # Delay between message deletions

    async def clear_channel_messages(self, channel: discord.TextChannel) -> None:
        logger.info(
            LogArea.SCHEDULER,
            f"Starting message clear for channel {channel.id} in guild {channel.guild.id}"
        )

        # Check permissions
        if not await self._check_permissions(channel):
            return

        # Perform the clear
        deleted_count = await self._delete_messages(channel)

        # Update next run time
        await self._update_next_run_time(channel)

        logger.info(LogArea.SCHEDULER, f"Cleared {deleted_count} messages from channel {channel.id}")

    async def _check_permissions(self, channel: discord.TextChannel) -> bool:
        permissions = channel.permissions_for(channel.guild.me)

        if not permissions.manage_messages:
            logger.warning(LogArea.PERMISSIONS, f"Missing 'Manage Messages' permission in channel {channel.id}")
            return False

        if not permissions.read_message_history:
            logger.warning(LogArea.PERMISSIONS, f"Missing 'Read Message History' permission in channel {channel.id}")
            return False

        if not permissions.read_messages:
            logger.warning(LogArea.PERMISSIONS, f"Missing 'Read Messages' permission in channel {channel.id}")
            return False

        return True

    async def _delete_messages(self, channel: discord.TextChannel) -> int:
        deleted_count = 0

        try:
            # Try bulk delete first (for messages < 14 days old)
            two_weeks_ago = discord.utils.utcnow() - timedelta(days=13)

            # Collect messages for bulk delete
            messages_to_delete = []
            old_messages = []

            async for message in channel.history(limit=None):
                if message.created_at > two_weeks_ago:
                    messages_to_delete.append(message)
                else:
                    old_messages.append(message)

            # Bulk delete newer messages
            if messages_to_delete:
                # Discord allows bulk delete of up to 100 messages at a time
                for i in range(0, len(messages_to_delete), 100):
                    batch = messages_to_delete[i : i + 100]
                    try:
                        await channel.delete_messages(batch)
                        deleted_count += len(batch)
                    except discord.HTTPException as e:
                        logger.warning(
                            LogArea.DISCORD,
                            f"Bulk delete failed: {e}, falling back to individual deletion"
                        )
                        for msg in batch:
                            try:
                                await msg.delete()
                                deleted_count += 1
                                await asyncio.sleep(self.rate_limit_delay)
                            except discord.HTTPException:
                                pass

            # Delete old messages individually
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
                channel_id=str(channel.id)
            )
            logger.error(LogArea.SCHEDULER, f"Error clearing messages in channel {channel.id}. Error ID: {error_id}")

        return deleted_count

    async def _update_next_run_time(self, channel: discord.TextChannel) -> None:
        server_id = str(channel.guild.id)
        channel_id = str(channel.id)

        # Get the job's next run time
        next_run_time = self.scheduler_service.get_next_run_time(server_id, channel_id)

        if not next_run_time:
            return

        # Update in data service
        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            server.channels[channel_id].next_run_time = next_run_time.astimezone(
                pytz.UTC
            )
            await self.data_service.save_servers()

    async def notify_missed_clear(
        self, channel: discord.TextChannel, job_id: str
    ) -> None:
        try:
            embed = discord.Embed(
                title="⚠️ Missed Clear Notification",
                description=(
                    "A scheduled message clear was missed for this channel.\n"
                    "The timer has been rescheduled."
                ),
                color=discord.Color.yellow(),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_footer(text=f"Job ID: {job_id}")

            await channel.send(embed=embed, delete_after=60)
        except discord.HTTPException:
            logger.warning(LogArea.SCHEDULER, f"Could not send missed clear notification to channel {channel.id}")
