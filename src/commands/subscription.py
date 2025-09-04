import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from src.utils.schedule_parser import ScheduleParseError
from src.utils.ignore_target_parser import identify_and_validate_ignore_target, validate_and_add_ignore_target
from src.utils.command_validation import CommandValidator, ValidationCheck


class SubscriptionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.scheduler_service = bot.scheduler_service
        self.schedule_parser = bot.scheduler_service.schedule_parser
        self.validator = CommandValidator(bot)
        
        # Add context menu commands
        self.add_context_menus()

    def add_context_menus(self):
        """Add context menu commands to the bot"""
        # Message context menu - Ignore Message
        @self.bot.tree.context_menu(name='Ignore Message')
        async def ignore_message_context(interaction: discord.Interaction, message: discord.Message):
            await self.handle_ignore_message_context(interaction, message)
        
        # User context menu - Ignore User
        @self.bot.tree.context_menu(name='Ignore User')
        async def ignore_user_context(interaction: discord.Interaction, user: discord.User):
            await self.handle_ignore_user_context(interaction, user)
    
    async def handle_ignore_message_context(self, interaction: discord.Interaction, message: discord.Message):
        """Handle the ignore message context menu command"""
        # Check if user has manage_messages permission
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ You need the **Manage Messages** permission to use this command.",
                ephemeral=True
            )
            return
        
        # Check if channel is subscribed
        server_id = str(interaction.guild.id)
        channel_id = str(message.channel.id)
        
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            await interaction.response.send_message(
                f"❌ {message.channel.mention} is not subscribed to automatic message clearing.\n"
                f"Use `/subscription add` to subscribe the channel first.",
                ephemeral=True
            )
            return
        
        channel_timer = server.channels[channel_id]
        message_id = str(message.id)
        
        # Toggle ignore status
        if message_id in channel_timer.ignored.messages:
            # Remove from ignored
            channel_timer.remove_ignored_message(message_id)
            await self.data_service.save_servers()
            
            await interaction.response.send_message(
                f"✅ Message from {message.author.mention} will **no longer be ignored** during clearing in {message.channel.mention}",
                ephemeral=True
            )
        else:
            # Add to ignored
            channel_timer.add_ignored_message(message_id)
            await self.data_service.save_servers()
            
            await interaction.response.send_message(
                f"✅ Message from {message.author.mention} will be **ignored** during clearing in {message.channel.mention}\n"
                f"Message ID: `{message_id}`",
                ephemeral=True
            )
    
    async def handle_ignore_user_context(self, interaction: discord.Interaction, user: discord.User):
        """Handle the ignore user context menu command"""
        # Check if user has manage_messages permission
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ You need the **Manage Messages** permission to use this command.",
                ephemeral=True
            )
            return
        
        # Get the channel where the context menu was invoked
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command can only be used in text channels.",
                ephemeral=True
            )
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)
        
        # Check if channel is subscribed
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to automatic message clearing.\n"
                f"Use `/subscription add` to subscribe the channel first.",
                ephemeral=True
            )
            return
        
        channel_timer = server.channels[channel_id]
        user_id = str(user.id)
        
        # Toggle ignore status
        if user_id in channel_timer.ignored.users:
            # Remove from ignored
            channel_timer.remove_ignored_user(user_id)
            await self.data_service.save_servers()
            
            await interaction.response.send_message(
                f"✅ Messages from {user.mention} will **no longer be ignored** during clearing in {channel.mention}",
                ephemeral=True
            )
        else:
            # Add to ignored
            channel_timer.add_ignored_user(user_id)
            await self.data_service.save_servers()
            
            await interaction.response.send_message(
                f"✅ Messages from {user.mention} will be **ignored** during clearing in {channel.mention}\n"
                f"User ID: `{user_id}`",
                ephemeral=True
            )

    # Create the main /subscription command group
    subscription_group = app_commands.Group(name="subscription", description="Manage automatic message clearing for channels")

    @subscription_group.command(
        name="add",
        description="Subscribe a channel to automatic message deletion"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        timer="Timer format: '24' for hours, '1d12h30m', or '15:30 EST' for daily at specific time",
        target_channel="Channel to clear (defaults to current channel)",
        ignored_target="Message ID/link or user mention/ID to ignore during clearing (optional)",
    )
    async def subscription_add(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
        ignored_target: Optional[str] = None,
    ):
        # Validate command with required checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
            ValidationCheck.BOT_PERMISSIONS: True,
            ValidationCheck.CHANNEL_NOT_SUBSCRIBED: True,
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Parse timer
        try:
            trigger, next_run_time = self.schedule_parser.parse_schedule_expression(timer, server_id)
        except ScheduleParseError as e:
            from src.components.subscription import InvalidTimerView
            view = InvalidTimerView(str(e))
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        # If timer is a time without timezone (e.g., "15:30"), append server timezone
        timer_to_store = timer
        if self.schedule_parser.TIMEZONE_PATTERN.match(timer.strip()):
            match = self.schedule_parser.TIMEZONE_PATTERN.match(timer.strip())
            if match and not match.group(2):  # No timezone specified
                server_timezone = self.data_service.get_timezone_for_server(server_id, None)
                if server_timezone and server_timezone != "UTC":
                    # Get timezone abbreviation from the full timezone string
                    import pytz
                    from datetime import datetime
                    tz = pytz.timezone(server_timezone)
                    # Get the current timezone abbreviation (handles DST)
                    tz_abbr = datetime.now(tz).strftime('%Z')
                    timer_to_store = f"{timer.strip()} {tz_abbr}"

        # Add to scheduler
        self.scheduler_service.create_channel_clear_job(
            channel_id=channel_id,
            server_id=server_id,
            trigger=trigger,
            channel=channel,
            next_run_time=next_run_time,
        )

        # Save to data service
        server = await self.data_service.get_server(server_id)
        if not server:
            server = await self.data_service.add_server(interaction.guild)

        server.add_channel(channel_id, timer_to_store, next_run_time)
        
        # Add ignored target if provided (message or user)
        ignored_entity_id, ignored_entity_type = await validate_and_add_ignore_target(
            ignored_target, channel, interaction.guild, server.channels[channel_id]
        )
        
        await self.data_service.save_servers()

        # Send success message
        from src.components.subscription import SubscriptionSuccessView
        
        view = SubscriptionSuccessView(channel, timer_to_store, next_run_time, ignored_entity_id, ignored_entity_type)
        await interaction.response.send_message(view=view)

    @subscription_group.command(
        name="remove",
        description="Unsubscribe a channel from automatic message deletion"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        target_channel="Channel to unsubscribe (defaults to current channel)"
    )
    async def subscription_remove(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Validate command with required checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
            ValidationCheck.BOT_PERMISSIONS: True,
            ValidationCheck.CHANNEL_SUBSCRIBED: "❌ {channel} is not subscribed to message deletion.",
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Remove from scheduler
        self.scheduler_service.remove_channel_clear_job(server_id, channel_id)

        # Remove from data service
        server = await self.data_service.get_server(server_id)
        if server:
            server.remove_channel(channel_id)
            await self.data_service.save_servers()

        # Send success message
        from src.components.subscription import UnsubscribeSuccessView
        
        view = UnsubscribeSuccessView(channel)
        await interaction.response.send_message(view=view)

    @subscription_group.command(
        name="list",
        description="List all active subscriptions in this server"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def subscription_list(
        self,
        interaction: discord.Interaction,
    ):
        # Validate command - only blacklist check for list
        checks = {
            ValidationCheck.BLACKLIST: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return

        server_id = str(interaction.guild.id)
        server = await self.data_service.get_server(server_id)
        
        if not server or not server.channels:
            from src.components.subscription import NoActiveSubscriptionsView
            view = NoActiveSubscriptionsView()
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Build list of subscriptions
        from src.components.subscription import SubscriptionListView
        
        view = SubscriptionListView(interaction.guild, server.channels, self.scheduler_service)
        await interaction.response.send_message(view=view)

    @subscription_group.command(
        name="info",
        description="View detailed subscription information for a channel"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        target_channel="Channel to check (defaults to current channel)"
    )
    async def subscription_info(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Validate command - only blacklist check for info
        checks = {
            ValidationCheck.BLACKLIST: True,
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Get next run time
        next_run_time = self.scheduler_service.get_channel_next_clear_time(server_id, channel_id)

        if not next_run_time:
            from src.components.subscription import ChannelNotSubscribedView
            view = ChannelNotSubscribedView(channel)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Get detailed subscription info from data service
        server = await self.data_service.get_server(server_id)
        timer_info = server.get_channel(channel_id) if server else None

        # Subscription info display
        from src.components.subscription import SubscriptionInfoView
        
        view = SubscriptionInfoView(channel, next_run_time, timer_info)
        await interaction.response.send_message(view=view)

    @subscription_group.command(
        name="update",
        description="Update the timer for an existing subscription"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        timer="New timer format: '24' for hours, '1d12h30m', or '15:30 EST' for daily at specific time",
        target_channel="Channel to update (defaults to current channel)",
        ignored_target="Message ID/link or user mention/ID to add to ignore list (optional)",
    )
    async def subscription_update(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
        ignored_target: Optional[str] = None,
    ):
        # Validate command with required checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
            ValidationCheck.BOT_PERMISSIONS: True,
            ValidationCheck.CHANNEL_SUBSCRIBED: True,
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Parse new timer
        try:
            trigger, next_run_time = self.schedule_parser.parse_schedule_expression(timer, server_id)
        except ScheduleParseError as e:
            from src.components.subscription import InvalidTimerView
            view = InvalidTimerView(str(e))
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Get current ignored messages
        server = await self.data_service.get_server(server_id)
        current_ignored_messages = []
        if server and channel_id in server.channels:
            current_ignored_messages = list(server.channels[channel_id].ignored_messages)

        # Remove old job
        self.scheduler_service.remove_channel_clear_job(server_id, channel_id)

        # Add new job with updated timer
        self.scheduler_service.create_channel_clear_job(
            channel_id=channel_id,
            server_id=server_id,
            trigger=trigger,
            channel=channel,
            next_run_time=next_run_time,
        )

        # If timer is a time without timezone (e.g., "15:30"), append server timezone
        timer_to_store = timer
        if self.schedule_parser.TIMEZONE_PATTERN.match(timer.strip()):
            match = self.schedule_parser.TIMEZONE_PATTERN.match(timer.strip())
            if match and not match.group(2):  # No timezone specified
                server_timezone = self.data_service.get_timezone_for_server(server_id, None)
                if server_timezone and server_timezone != "UTC":
                    # Get timezone abbreviation from the full timezone string
                    import pytz
                    from datetime import datetime
                    tz = pytz.timezone(server_timezone)
                    # Get the current timezone abbreviation (handles DST)
                    tz_abbr = datetime.now(tz).strftime('%Z')
                    timer_to_store = f"{timer.strip()} {tz_abbr}"
        
        # Update in data service
        if server:
            server.channels[channel_id].timer = timer_to_store
            server.channels[channel_id].next_run_time = next_run_time
            
            # Restore ignored messages
            for msg_id in current_ignored_messages:
                server.channels[channel_id].add_ignored_message(msg_id)
            
            # Add new ignored target if provided (message or user)
            ignored_entity_id, ignored_entity_type = await validate_and_add_ignore_target(
                ignored_target, channel, interaction.guild, server.channels[channel_id]
            )
            
            await self.data_service.save_servers()

        # Send success message
        from src.components.subscription import UpdateSuccessView
        view = UpdateSuccessView(channel, timer_to_store, next_run_time, ignored_entity_id, ignored_entity_type)
        await interaction.response.send_message(view=view)

    @subscription_group.command(
        name="ignore",
        description="Toggle a message or user to be ignored during channel clearing"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        target="Message ID/link or user mention/ID to toggle ignore status",
        target_channel="Channel with the subscription (defaults to current channel)"
    )
    async def subscription_ignore(
        self,
        interaction: discord.Interaction,
        target: str,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Validate command with required checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
            ValidationCheck.BOT_PERMISSIONS: True,
            ValidationCheck.CHANNEL_SUBSCRIBED: "❌ {channel} is not subscribed to message deletion. Use `/subscription add` to subscribe first.",
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Parse and validate the target
        entity_id, entity_type = await identify_and_validate_ignore_target(target, channel, interaction.guild)
        
        if not entity_id:
            from src.components.subscription import InvalidTargetView
            view = InvalidTargetView()
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Get server and channel data
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            from src.components.subscription import NoSubscriptionDataView
            view = NoSubscriptionDataView(channel)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        channel_timer = server.channels[channel_id]
        
        if entity_type == "user":
            # Handle user toggle
            if entity_id in channel_timer.ignored.users:
                # Remove the user
                channel_timer.remove_ignored_user(entity_id)
                await self.data_service.save_servers()
                
                from src.components.subscription import IgnoreEntityView
                view = IgnoreEntityView("User", entity_id, channel, added=False)
                await interaction.response.send_message(view=view)
            else:
                # Verify user exists in the guild (double-check)
                try:
                    member = await interaction.guild.fetch_member(int(entity_id))
                    if not member:
                        from src.components.subscription import UserNotFoundView
                        view = UserNotFoundView(entity_id)
                        await interaction.response.send_message(view=view, ephemeral=True)
                        return
                except (discord.NotFound, discord.HTTPException, ValueError):
                    from src.components.subscription import UserNotFoundView
                    view = UserNotFoundView(entity_id)
                    await interaction.response.send_message(view=view, ephemeral=True)
                    return
                
                # Add the user
                channel_timer.add_ignored_user(entity_id)
                await self.data_service.save_servers()
                
                from src.components.subscription import IgnoreEntityView
                view = IgnoreEntityView("User", entity_id, channel, added=True)
                await interaction.response.send_message(view=view)
        else:  # message
            # Handle message toggle
            if entity_id in channel_timer.ignored_messages:
                # Remove the message
                channel_timer.remove_ignored_message(entity_id)
                await self.data_service.save_servers()
                
                from src.components.subscription import IgnoreEntityView
                view = IgnoreEntityView("Message", entity_id, channel, added=False)
                await interaction.response.send_message(view=view)
            else:
                # Check if message exists in the channel before adding
                try:
                    message = await channel.fetch_message(int(entity_id))
                    if not message:
                        from src.components.subscription import MessageNotFoundView
                        view = MessageNotFoundView(entity_id, channel)
                        await interaction.response.send_message(view=view, ephemeral=True)
                        return
                except (discord.NotFound, discord.HTTPException, ValueError):
                    from src.components.subscription import MessageNotFoundView
                    view = MessageNotFoundView(entity_id, channel)
                    await interaction.response.send_message(view=view, ephemeral=True)
                    return
                
                # Add the message
                channel_timer.add_ignored_message(entity_id)
                await self.data_service.save_servers()
                
                from src.components.subscription import IgnoreEntityView
                view = IgnoreEntityView("Message", entity_id, channel, added=True)
                await interaction.response.send_message(view=view)

    @subscription_group.command(
        name="clear",
        description="Manually trigger a message clear for a subscribed channel"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        target_channel="Channel to clear (defaults to current channel)"
    )
    async def subscription_clear_now(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Validate command with required checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
            ValidationCheck.BOT_PERMISSIONS: True,
            ValidationCheck.CHANNEL_SUBSCRIBED: True,
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Defer the response as clearing might take time
        await interaction.response.defer(ephemeral=True)

        # Get ignored messages and users
        server = await self.data_service.get_server(server_id)
        ignored_messages = []
        ignored_users = []
        if server and channel_id in server.channels:
            channel_timer = server.channels[channel_id]
            ignored_messages = list(channel_timer.ignored.messages)
            ignored_users = list(channel_timer.ignored.users)

        # Trigger the clear using MessageService directly
        from src.services.message_clearing_service import MessageService
        message_service = MessageService(self.bot.data_service, self.bot.scheduler_service)
        deleted_count = await message_service._perform_message_deletion(channel, set(ignored_messages), set(ignored_users))

        # Send result
        from src.components.subscription import ManualClearSuccessView
        view = ManualClearSuccessView(deleted_count, channel)
        await interaction.followup.send(view=view, ephemeral=True)

    @subscription_group.command(
        name="skip",
        description="Skip the next scheduled clear for a channel"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        target_channel="Channel to skip next clear (defaults to current channel)"
    )
    async def subscription_skip_next(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Validate command with required checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
            ValidationCheck.BOT_PERMISSIONS: True,
            ValidationCheck.CHANNEL_SUBSCRIBED: True,
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Get the current job to retrieve its trigger
        job = self.scheduler_service.get_channel_clear_job(server_id, channel_id)
        if not job:
            from src.components.subscription import JobNotFoundView
            view = JobNotFoundView(channel)
            await interaction.response.send_message(view=view, ephemeral=True)
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
            from src.components.subscription import NextTimeNotFoundView
            view = NextTimeNotFoundView(channel)
            await interaction.response.send_message(view=view, ephemeral=True)

    # Legacy methods moved to command_validation.py and target_parser utility
    def _parse_message_id_from_input(self, message_input: str) -> Optional[str]:
        """Extract message ID from either a message link or direct ID"""
        from src.utils.ignore_target_parser import extract_discord_message_id
        return extract_discord_message_id(message_input)
    
    def _parse_user_id_from_input(self, user_input: str) -> Optional[str]:
        """Extract user ID from mention or direct ID"""
        from src.utils.ignore_target_parser import extract_discord_user_id
        return extract_discord_user_id(user_input)


async def setup(bot):
    await bot.add_cog(SubscriptionCommands(bot))