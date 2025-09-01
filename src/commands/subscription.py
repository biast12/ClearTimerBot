import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from src.utils.timer_parser import TimerParseError


class SubscriptionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.scheduler_service = bot.scheduler_service
        self.timer_parser = bot.scheduler_service.timer_parser

    # Create the main /sub command group
    sub_group = app_commands.Group(name="sub", description="Manage channel message clearing subscriptions")

    @sub_group.command(
        name="add",
        description="Subscribe a channel to automatic message deletion"
    )
    @app_commands.describe(
        timer="Timer format: '24' for hours, '1d12h30m', or '15:30 EST' for daily at specific time",
        target_channel="Channel to clear (defaults to current channel)",
        ignored_message="Message ID or link to ignore during clearing (optional)",
    )
    async def sub_add(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
        ignored_message: Optional[str] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if already subscribed
        if self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} already has a timer set. Use `/sub remove` to remove it first.",
                ephemeral=True,
            )
            return

        # Parse timer
        try:
            trigger, next_run_time = self.timer_parser.parse(timer)
        except TimerParseError as e:
            await interaction.response.send_message(
                f"❌ Invalid timer: {e}", ephemeral=True
            )
            return

        # Add to scheduler
        self.scheduler_service.add_job(
            channel_id=channel_id,
            server_id=server_id,
            trigger=trigger,
            channel=channel,
            next_run_time=next_run_time,
        )

        # Save to data service
        server = await self.data_service.get_server(server_id)
        if not server:
            server = await self.data_service.add_server(
                server_id, interaction.guild.name
            )

        server.add_channel(channel_id, timer, next_run_time)
        
        # Add ignored message if provided
        message_id = None
        if ignored_message:
            message_id = self._extract_message_id(ignored_message)
            if message_id:
                server.channels[channel_id].add_ignored_message(message_id)
        
        await self.data_service.save_servers()

        # Send success message
        from src.components.subscription import SubscriptionSuccessView
        
        view = SubscriptionSuccessView(channel, timer, next_run_time, message_id)
        await interaction.response.send_message(view=view)

    @sub_group.command(
        name="remove",
        description="Unsubscribe a channel from automatic message deletion"
    )
    @app_commands.describe(
        target_channel="Channel to unsubscribe (defaults to current channel)"
    )
    async def sub_remove(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if subscribed
        if not self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion.",
                ephemeral=True,
            )
            return

        # Remove from scheduler
        self.scheduler_service.remove_job(server_id, channel_id)

        # Remove from data service
        server = await self.data_service.get_server(server_id)
        if server:
            server.remove_channel(channel_id)
            await self.data_service.save_servers()

        # Send success message
        from src.components.subscription import UnsubscribeSuccessView
        
        view = UnsubscribeSuccessView(channel)
        await interaction.response.send_message(view=view)

    @sub_group.command(
        name="info",
        description="View detailed subscription information for a channel"
    )
    @app_commands.describe(
        target_channel="Channel to check (defaults to current channel)"
    )
    async def sub_info(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Get next run time
        next_run_time = self.scheduler_service.get_next_run_time(server_id, channel_id)

        if not next_run_time:
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion.\n"
                f"Use `/sub add` to set up automatic clearing.",
                ephemeral=True,
            )
            return

        # Get detailed subscription info from data service
        server = await self.data_service.get_server(server_id)
        timer_info = server.get_channel(channel_id) if server else None

        # Use Components v2 for subscription info display
        from src.components.subscription import SubscriptionInfoView
        
        view = SubscriptionInfoView(channel, next_run_time, timer_info)
        await interaction.response.send_message(view=view)

    @sub_group.command(
        name="ignore",
        description="Toggle a message to be ignored during channel clearing"
    )
    @app_commands.describe(
        message="Message ID or link to toggle ignore status",
        target_channel="Channel with the subscription (defaults to current channel)"
    )
    async def sub_ignore(
        self,
        interaction: discord.Interaction,
        message: str,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if channel is subscribed
        if not self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion. Use `/sub add` first.",
                ephemeral=True,
            )
            return

        # Extract message ID
        message_id = self._extract_message_id(message)
        if not message_id:
            await interaction.response.send_message(
                "❌ Invalid message ID or link format. Please provide a valid message ID or Discord message link.",
                ephemeral=True,
            )
            return

        # Get server and channel data
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            await interaction.response.send_message(
                f"❌ Could not find subscription data for {channel.mention}.",
                ephemeral=True,
            )
            return

        channel_timer = server.channels[channel_id]
        
        # Toggle logic - remove if exists, add if doesn't exist
        if message_id in channel_timer.ignored_messages:
            # Remove the message
            channel_timer.remove_ignored_message(message_id)
            await self.data_service.save_servers()
            
            from src.components.subscription import IgnoreMessageView
            view = IgnoreMessageView("Message Removed from Ignore List", message_id, channel, added=False)
            await interaction.response.send_message(view=view)
        else:
            # Add the message
            channel_timer.add_ignored_message(message_id)
            await self.data_service.save_servers()
            
            from src.components.subscription import IgnoreMessageView
            view = IgnoreMessageView("Message Added to Ignore List", message_id, channel, added=True)
            await interaction.response.send_message(view=view)

    @sub_group.command(
        name="list",
        description="List all active subscriptions in this server"
    )
    async def sub_list(
        self,
        interaction: discord.Interaction,
    ):
        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        server_id = str(interaction.guild.id)
        server = await self.data_service.get_server(server_id)
        
        if not server or not server.channels:
            await interaction.response.send_message(
                "❌ No active subscriptions found in this server.\n"
                "Use `/sub add` to subscribe a channel to automatic clearing.",
                ephemeral=True,
            )
            return

        # Build list of subscriptions
        from src.components.subscription import SubscriptionListView
        
        view = SubscriptionListView(interaction.guild, server.channels, self.scheduler_service)
        await interaction.response.send_message(view=view)

    @sub_group.command(
        name="clear",
        description="Manually trigger a message clear for a subscribed channel"
    )
    @app_commands.describe(
        target_channel="Channel to clear (defaults to current channel)"
    )
    async def sub_clear(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if channel is subscribed
        if not self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion.\n"
                f"Use `/sub add` to set up automatic clearing first.",
                ephemeral=True,
            )
            return

        # Defer the response as clearing might take time
        await interaction.response.defer(ephemeral=True)

        # Get ignored messages
        server = await self.data_service.get_server(server_id)
        ignored_messages = []
        if server and channel_id in server.channels:
            ignored_messages = list(server.channels[channel_id].ignored_messages)

        # Trigger the clear
        from src.services.clear_service import ClearService
        clear_service = ClearService(self.bot)
        deleted_count = await clear_service.clear_channel(channel, ignored_messages)

        # Send result
        await interaction.followup.send(
            f"✅ Manually cleared {deleted_count} message(s) from {channel.mention}.",
            ephemeral=True,
        )

    @sub_group.command(
        name="skip",
        description="Skip the next scheduled clear for a channel"
    )
    @app_commands.describe(
        target_channel="Channel to skip next clear (defaults to current channel)"
    )
    async def sub_skip(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if channel is subscribed
        if not self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion.\n"
                f"Use `/sub add` to set up automatic clearing first.",
                ephemeral=True,
            )
            return

        # Get the current job to retrieve its trigger
        job = self.scheduler_service.get_job(server_id, channel_id)
        if not job:
            await interaction.response.send_message(
                f"❌ Could not find the scheduled job for {channel.mention}.",
                ephemeral=True,
            )
            return

        # Calculate the next run time after the current one
        next_run_time = job.next_run_time
        if next_run_time:
            # Reschedule to skip one occurrence
            job.modify(next_run_time=job.trigger.get_next_fire_time(next_run_time, next_run_time))
            
            # Update in data service
            server = await self.data_service.get_server(server_id)
            if server and channel_id in server.channels:
                server.channels[channel_id].next_run_time = job.next_run_time
                await self.data_service.save_servers()
            
            # Send success message with new time
            from src.components.subscription import SkipSuccessView
            view = SkipSuccessView(channel, job.next_run_time)
            await interaction.response.send_message(view=view)
        else:
            await interaction.response.send_message(
                f"❌ Could not determine the next scheduled time for {channel.mention}.",
                ephemeral=True,
            )

    @sub_group.command(
        name="update",
        description="Update the timer for an existing subscription"
    )
    @app_commands.describe(
        timer="New timer format: '24' for hours, '1d12h30m', or '15:30 EST' for daily at specific time",
        target_channel="Channel to update (defaults to current channel)",
        ignored_message="Message ID or link to add to ignore list (optional)",
    )
    async def sub_update(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
        ignored_message: Optional[str] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if channel is subscribed
        if not self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion.\n"
                f"Use `/sub add` to set up automatic clearing first.",
                ephemeral=True,
            )
            return

        # Parse new timer
        try:
            trigger, next_run_time = self.timer_parser.parse(timer)
        except TimerParseError as e:
            await interaction.response.send_message(
                f"❌ Invalid timer: {e}", ephemeral=True
            )
            return

        # Get current ignored messages
        server = await self.data_service.get_server(server_id)
        current_ignored_messages = []
        if server and channel_id in server.channels:
            current_ignored_messages = list(server.channels[channel_id].ignored_messages)

        # Remove old job
        self.scheduler_service.remove_job(server_id, channel_id)

        # Add new job with updated timer
        self.scheduler_service.add_job(
            channel_id=channel_id,
            server_id=server_id,
            trigger=trigger,
            channel=channel,
            next_run_time=next_run_time,
        )

        # Update in data service
        if server:
            server.channels[channel_id].timer = timer
            server.channels[channel_id].next_run_time = next_run_time
            
            # Restore ignored messages
            for msg_id in current_ignored_messages:
                server.channels[channel_id].add_ignored_message(msg_id)
            
            # Add new ignored message if provided
            message_id = None
            if ignored_message:
                message_id = self._extract_message_id(ignored_message)
                if message_id and message_id not in current_ignored_messages:
                    server.channels[channel_id].add_ignored_message(message_id)
            
            await self.data_service.save_servers()

        # Send success message
        from src.components.subscription import UpdateSuccessView
        view = UpdateSuccessView(channel, timer, next_run_time, message_id)
        await interaction.response.send_message(view=view)

    async def _check_permissions(self, interaction: discord.Interaction, target_channel: discord.TextChannel = None) -> bool:
        member = interaction.guild.get_member(interaction.user.id)

        # Bot owner bypasses user permission checks
        if not self.bot.is_owner(interaction.user):
            # Check if user has manage_messages permission
            if not member.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    "❌ You need the `Manage Messages` permission to use this command.",
                    ephemeral=True,
                )
                return False

        # Check bot permissions in the target channel
        channel = target_channel or interaction.channel
        bot_permissions = channel.permissions_for(interaction.guild.me)
        
        required_perms = {
            'view_channel': bot_permissions.view_channel,
            'send_messages': bot_permissions.send_messages,
            'read_message_history': bot_permissions.read_message_history,
            'manage_messages': bot_permissions.manage_messages,
            'embed_links': bot_permissions.embed_links,
            'use_application_commands': bot_permissions.use_application_commands,
            'send_messages_in_threads': bot_permissions.send_messages_in_threads
        }
        
        missing_perms = [perm.replace('_', ' ').title() for perm, has_perm in required_perms.items() if not has_perm]
        
        if missing_perms:
            await interaction.response.send_message(
                f"❌ I'm missing the following permissions in {channel.mention}: {', '.join(missing_perms)}",
                ephemeral=True,
            )
            return False

        return True

    async def _is_blacklisted(self, interaction: discord.Interaction) -> bool:
        server_id = str(interaction.guild.id)

        if await self.data_service.is_blacklisted(server_id):
            await interaction.response.send_message(
                "❌ This server has been blacklisted and cannot use this bot.",
                ephemeral=True,
            )
            return True

        return False
    
    def _extract_message_id(self, message_input: str) -> Optional[str]:
        """Extract message ID from either a message link or direct ID"""
        import re
        
        # Check if it's a message link
        link_pattern = r"https://discord(?:app)?\.com/channels/\d+/\d+/(\d+)"
        match = re.match(link_pattern, message_input)
        if match:
            return match.group(1)
        
        # Check if it's a direct message ID (digits only)
        if message_input.isdigit():
            return message_input
        
        return None


async def setup(bot):
    await bot.add_cog(SubscriptionCommands(bot))