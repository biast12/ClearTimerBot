import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from discord.ext.commands import Bot

from src.utils.schedule_parser import ScheduleParseError
from src.utils.ignore_target_parser import (
    identify_and_validate_multiple_ignore_targets,
    validate_and_add_multiple_ignore_targets
)
from src.utils.command_validation import CommandValidator, ValidationCheck
from src.localization import get_translator
from src.utils.logger import logger, LogArea


class SubscriptionCommands(commands.Cog):
    def __init__(self, bot: 'Bot') -> None:
        self.bot = bot
        self.data_service = bot.data_service
        self.scheduler_service = bot.scheduler_service
        self.schedule_parser = bot.scheduler_service.schedule_parser
        self.validator = CommandValidator(bot)
        
        # Add context menu commands
        self.add_context_menus()

    def add_context_menus(self) -> None:
        @self.bot.tree.context_menu(name='Ignore Message')
        async def ignore_message_context(interaction: discord.Interaction, message: discord.Message):
            await self.handle_ignore_message_context(interaction, message)
        
        @self.bot.tree.context_menu(name='Ignore User')
        async def ignore_user_context(interaction: discord.Interaction, user: discord.User):
            await self.handle_ignore_user_context(interaction, user)
    
    async def handle_ignore_message_context(self, interaction: discord.Interaction, message: discord.Message) -> None:
        # Validate command with blacklist and permission checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        
        # Check if channel is subscribed
        server_id = str(interaction.guild.id)
        channel_id = str(message.channel.id)
        
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            await interaction.response.send_message(
                translator.get("validation.not_subscribed", channel=message.channel.mention),
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
                translator.get("commands.subscription.ignore.message_removed", 
                              author=message.author.mention, 
                              channel=message.channel.mention),
                ephemeral=True
            )
        else:
            # Add to ignored
            channel_timer.add_ignored_message(message_id)
            await self.data_service.save_servers()
            
            await interaction.response.send_message(
                translator.get("commands.subscription.ignore.message_added",
                              author=message.author.mention,
                              channel=message.channel.mention,
                              message_id=message_id),
                ephemeral=True
            )
    
    async def handle_ignore_user_context(self, interaction: discord.Interaction, user: discord.User) -> None:
        """Handle the ignore user context menu command"""
        # Validate command with blacklist and permission checks
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        
        # Get the channel where the context menu was invoked
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                translator.get("validation.invalid_channel"),
                ephemeral=True
            )
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)
        
        # Check if channel is subscribed
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            await interaction.response.send_message(
                translator.get("validation.not_subscribed", channel=channel.mention),
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
                translator.get("commands.subscription.ignore.user_removed",
                              user=user.mention,
                              channel=channel.mention),
                ephemeral=True
            )
        else:
            # Add to ignored
            channel_timer.add_ignored_user(user_id)
            await self.data_service.save_servers()
            
            await interaction.response.send_message(
                translator.get("commands.subscription.ignore.user_added",
                              user=user.mention,
                              channel=channel.mention),
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
        ignored_target="Message IDs/links or user mentions/IDs (comma-separated for multiple)",
        view="Show persistent timer message that updates after each clear",
    )
    async def subscription_add(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
        ignored_target: Optional[str] = None,
        view: Optional[bool] = False,
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
        translator = await get_translator(server_id, self.data_service)

        # Parse timer
        try:
            trigger, next_run_time = self.schedule_parser.parse_schedule_expression(timer, server_id)
        except ScheduleParseError as e:
            from src.components.subscription import InvalidTimerView
            view = InvalidTimerView(str(e), translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        # Store the timer as provided - the parser will handle timezone defaults
        timer_to_store = timer.strip()

        # Save to data service FIRST (before creating scheduler job)
        server = await self.data_service.get_server(server_id)
        if not server:
            server = await self.data_service.add_server(interaction.guild)

        server.add_channel(channel_id, timer_to_store, next_run_time)
        
        # Defer the response immediately (non-ephemeral so we can send a proper response)
        await interaction.response.defer(ephemeral=False)
        
        # Add ignored targets if provided (messages or users)
        added_targets = await validate_and_add_multiple_ignore_targets(
            ignored_target, channel, interaction.guild, server.channels[channel_id]
        )
        
        # Create view message if requested
        view_message = None
        if view:
            from src.components.subscription import TimerViewMessage
            timer_view = TimerViewMessage(channel, timer_to_store, next_run_time, translator)
            view_message = await channel.send(view=timer_view)
            
            # Store the view message ID
            server.channels[channel_id].view_message_id = str(view_message.id)
        
        # Save the data BEFORE creating the job to prevent race condition
        await self.data_service.save_servers()

        # Add to scheduler AFTER data is saved
        # This ensures ignored targets are persisted before any clearing can happen
        self.scheduler_service.create_channel_clear_job(
            channel_id=channel_id,
            server_id=server_id,
            trigger=trigger,
            channel=channel,
            next_run_time=next_run_time,
        )

        # Send success message using followup since we deferred
        from src.components.subscription import SubscriptionSuccessView, SubscriptionSuccessWithMultipleIgnoresView
        
        if len(added_targets) == 1:
            success_view = SubscriptionSuccessView(channel, timer_to_store, next_run_time, translator, added_targets[0][0], added_targets[0][1])
        elif len(added_targets) > 1:
            # Use a new view for multiple targets
            success_view = SubscriptionSuccessWithMultipleIgnoresView(channel, timer_to_store, next_run_time, added_targets, translator)
        else:
            success_view = SubscriptionSuccessView(channel, timer_to_store, next_run_time, translator, None, None)
        
        # Edit the deferred response - send just the view without extra content
        try:
            await interaction.edit_original_response(
                view=success_view
            )
        except Exception as e:
            logger.error(LogArea.SUBSCRIPTION, f"Error editing response: {e}")
            # Try followup as fallback
            try:
                await interaction.followup.send(
                    view=success_view
                )
            except Exception as e2:
                logger.error(LogArea.SUBSCRIPTION, f"Error with followup: {e2}")
                # Last resort - send without view
                await interaction.followup.send(
                    content=f"✅ Subscription {'created with persistent timer view' if view_message else 'created successfully'}."
                )

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
        translator = await get_translator(server_id, self.data_service)

        # Remove from scheduler
        self.scheduler_service.remove_channel_clear_job(server_id, channel_id)

        # Remove from data service and clean up view message
        server = await self.data_service.get_server(server_id)
        if server:
            # Delete view message if it exists
            if channel_id in server.channels:
                view_message_id = server.channels[channel_id].view_message_id
                if view_message_id:
                    try:
                        # Try cache first
                        cache_key = f"discord:msg:{channel.id}:{view_message_id}"
                        message = await self.data_service._cache.get(cache_key)
                        
                        if not message:
                            message = await channel.fetch_message(int(view_message_id))
                            # Cache briefly since we're about to delete it
                            await self.data_service._cache.set(cache_key, message, cache_level="memory", ttl=60)
                        
                        await message.delete()
                        # Invalidate cache after deletion
                        await self.data_service._cache.invalidate(cache_key)
                    except:
                        pass  # Message might have been deleted already
            
            server.remove_channel(channel_id)
            await self.data_service.save_servers()

        # Send success message
        from src.components.subscription import UnsubscribeSuccessView
        
        view = UnsubscribeSuccessView(channel, translator)
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
        # Validate command with permission check
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return

        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        server = await self.data_service.get_server(server_id)
        
        if not server or not server.channels:
            from src.components.subscription import NoActiveSubscriptionsView
            view = NoActiveSubscriptionsView(translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Build list of subscriptions
        from src.components.subscription import SubscriptionListView
        
        view = SubscriptionListView(interaction.guild, server.channels, self.scheduler_service, translator)
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
        # Validate command with permission check
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: True,
        }
        
        is_valid, error_msg, channel = await self.validator.validate_command(
            interaction, target_channel, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)
        translator = await get_translator(server_id, self.data_service)

        # Get next run time
        next_run_time = self.scheduler_service.get_channel_next_clear_time(server_id, channel_id)

        if not next_run_time:
            from src.components.subscription import ChannelNotSubscribedView
            view = ChannelNotSubscribedView(channel, translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Get detailed subscription info from data service
        server = await self.data_service.get_server(server_id)
        timer_info = server.get_channel(channel_id) if server else None

        # Subscription info display
        from src.components.subscription import SubscriptionInfoView
        
        view = SubscriptionInfoView(channel, next_run_time, timer_info, translator)
        await interaction.response.send_message(view=view)

    @subscription_group.command(
        name="update",
        description="Update the timer for an existing subscription"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        timer="New timer format: '24' for hours, '1d12h30m', or '15:30 EST' for daily at specific time",
        target_channel="Channel to update (defaults to current channel)",
        ignored_target="Message IDs/links or user mentions/IDs to add (comma-separated for multiple)",
        view="Show/update persistent timer message that updates after each clear",
    )
    async def subscription_update(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
        ignored_target: Optional[str] = None,
        view: Optional[bool] = False,
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
        translator = await get_translator(server_id, self.data_service)

        # Parse new timer
        try:
            trigger, next_run_time = self.schedule_parser.parse_schedule_expression(timer, server_id)
        except ScheduleParseError as e:
            from src.components.subscription import InvalidTimerView
            view = InvalidTimerView(str(e), translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Defer the response immediately (non-ephemeral so we can send a proper response)
        await interaction.response.defer(ephemeral=False)
        
        # Get current ignored messages and users
        server = await self.data_service.get_server(server_id)
        current_ignored_messages = []
        current_ignored_users = []
        old_view_message_id = None
        if server and channel_id in server.channels:
            current_ignored_messages = list(server.channels[channel_id].ignored.messages)
            current_ignored_users = list(server.channels[channel_id].ignored.users)
            old_view_message_id = server.channels[channel_id].view_message_id
        
        # Remove old job first
        self.scheduler_service.remove_channel_clear_job(server_id, channel_id)

        # Store the timer as provided - the parser will handle timezone defaults
        timer_to_store = timer.strip()
        
        # Update in data service
        if server:
            server.channels[channel_id].timer = timer_to_store
            server.channels[channel_id].next_run_time = next_run_time
            
            # Restore ignored messages and users
            for msg_id in current_ignored_messages:
                server.channels[channel_id].add_ignored_message(msg_id)
            for user_id in current_ignored_users:
                server.channels[channel_id].add_ignored_user(user_id)
            
            # Add new ignored targets if provided (messages or users)
            added_targets = await validate_and_add_multiple_ignore_targets(
                ignored_target, channel, interaction.guild, server.channels[channel_id]
            )
            
            # Handle view message BEFORE responding
            view_message = None
            from src.components.subscription import TimerViewMessage
            timer_view = TimerViewMessage(channel, timer_to_store, next_run_time, translator)
            
            if view:
                # Delete old view message if it exists
                if old_view_message_id:
                    try:
                        # Try cache first
                        cache_key = f"discord:msg:{channel.id}:{old_view_message_id}"
                        old_message = await self.data_service._cache.get(cache_key)
                        
                        if not old_message:
                            old_message = await channel.fetch_message(int(old_view_message_id))
                            # Cache briefly since we're about to delete it
                            await self.data_service._cache.set(cache_key, old_message, cache_level="memory", ttl=60)
                        
                        await old_message.delete()
                        # Invalidate cache after deletion
                        await self.data_service._cache.invalidate(cache_key)
                    except:
                        pass  # Message might have been deleted already
                
                # Create new view message
                view_message = await channel.send(view=timer_view)
                server.channels[channel_id].view_message_id = str(view_message.id)
            elif old_view_message_id:
                # User didn't specify view parameter but there's an existing view message
                # Update the existing view message
                try:
                    old_message = await channel.fetch_message(int(old_view_message_id))
                    await old_message.edit(view=timer_view)
                    view_message = old_message  # Track that we updated it
                except:
                    # If message doesn't exist, clear the ID
                    server.channels[channel_id].view_message_id = None
            
            # Save data BEFORE creating the new job to prevent race condition
            await self.data_service.save_servers()

        # Add new job with updated timer AFTER data is saved
        # This ensures ignored targets are persisted before any clearing can happen
        self.scheduler_service.create_channel_clear_job(
            channel_id=channel_id,
            server_id=server_id,
            trigger=trigger,
            channel=channel,
            next_run_time=next_run_time,
        )

        # Send success message
        from src.components.subscription import UpdateSuccessView, UpdateSuccessWithMultipleIgnoresView
        
        if len(added_targets) == 1:
            success_view = UpdateSuccessView(channel, timer_to_store, next_run_time, translator, added_targets[0][0], added_targets[0][1])
        elif len(added_targets) > 1:
            # Use a new view for multiple targets
            success_view = UpdateSuccessWithMultipleIgnoresView(channel, timer_to_store, next_run_time, added_targets, translator)
        else:
            success_view = UpdateSuccessView(channel, timer_to_store, next_run_time, translator, None, None)
        
        # Edit the deferred response - send just the view without extra content
        try:
            await interaction.edit_original_response(
                view=success_view
            )
        except Exception as e:
            logger.error(LogArea.SUBSCRIPTION, f"Error editing response: {e}")
            # Try followup as fallback
            try:
                await interaction.followup.send(
                    view=success_view
                )
            except Exception as e2:
                logger.error(LogArea.SUBSCRIPTION, f"Error with followup: {e2}")
                # Last resort - send without view
                await interaction.followup.send(
                    content=f"✅ Subscription {'updated with persistent timer view' if view_message else 'updated successfully'}."
                )

    @subscription_group.command(
        name="ignore",
        description="Toggle messages or users to be ignored during channel clearing"
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        target="Message IDs/links or user mentions/IDs (comma-separated for multiple)",
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
        translator = await get_translator(server_id, self.data_service)

        # Parse and validate multiple targets
        validated_targets = await identify_and_validate_multiple_ignore_targets(target, channel, interaction.guild)
        
        if not validated_targets:
            from src.components.subscription import InvalidTargetView
            view = InvalidTargetView(translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Get server and channel data
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            from src.components.subscription import NoSubscriptionDataView
            view = NoSubscriptionDataView(channel, translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        channel_timer = server.channels[channel_id]
        
        # Process all targets
        added_users = []
        removed_users = []
        added_messages = []
        removed_messages = []
        
        for entity_id, entity_type in validated_targets:
            if entity_type == "user":
                # Handle user toggle
                if entity_id in channel_timer.ignored.users:
                    # Remove the user
                    channel_timer.remove_ignored_user(entity_id)
                    removed_users.append(entity_id)
                else:
                    # Add the user
                    channel_timer.add_ignored_user(entity_id)
                    added_users.append(entity_id)
            else:  # message
                # Handle message toggle
                if entity_id in channel_timer.ignored.messages:
                    # Remove the message
                    channel_timer.remove_ignored_message(entity_id)
                    removed_messages.append(entity_id)
                else:
                    # Add the message
                    channel_timer.add_ignored_message(entity_id)
                    added_messages.append(entity_id)
        
        await self.data_service.save_servers()
        
        # Build response message
        from src.components.subscription import MultipleIgnoreEntityView
        view = MultipleIgnoreEntityView(
            channel,
            added_users,
            removed_users,
            added_messages,
            removed_messages,
            translator
        )
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
        translator = await get_translator(server_id, self.data_service)

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
        view = ManualClearSuccessView(deleted_count, channel, translator)
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
        translator = await get_translator(server_id, self.data_service)

        # Get the current job to retrieve its trigger
        job = self.scheduler_service.get_channel_clear_job(server_id, channel_id)
        if not job:
            from src.components.subscription import JobNotFoundView
            view = JobNotFoundView(channel, translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Calculate the next run time after the current one
        next_run_time = job.next_run_time
        if next_run_time:
            # Reschedule to skip one occurrence
            new_next_run_time = job.trigger.get_next_fire_time(next_run_time, next_run_time)
            self.scheduler_service.scheduler.modify_job(job.id, next_run_time=new_next_run_time)
            
            # Update in data service
            server = await self.data_service.get_server(server_id)
            if server and channel_id in server.channels:
                server.channels[channel_id].next_run_time = new_next_run_time
                
                # Update view message if it exists
                view_message_id = server.channels[channel_id].view_message_id
                if view_message_id:
                    try:
                        # Try to fetch and update the view message
                        view_message = await channel.fetch_message(int(view_message_id))
                        from src.components.subscription import TimerViewMessage
                        timer_view = TimerViewMessage(
                            channel, 
                            server.channels[channel_id].timer, 
                            new_next_run_time, 
                            translator
                        )
                        await view_message.edit(view=timer_view)
                    except:
                        # If message doesn't exist, clear the ID
                        server.channels[channel_id].view_message_id = None
                
                await self.data_service.save_servers()
            
            # Send success message with new time
            from src.components.subscription import SkipSuccessView
            view = SkipSuccessView(channel, new_next_run_time, translator)
            await interaction.response.send_message(view=view)
        else:
            from src.components.subscription import NextTimeNotFoundView
            view = NextTimeNotFoundView(channel, translator)
            await interaction.response.send_message(view=view, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(SubscriptionCommands(bot))