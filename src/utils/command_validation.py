import discord
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from discord.ext.commands import Bot


class ValidationCheck(Enum):
    BLACKLIST = "blacklist"
    USER_PERMISSIONS = "user_permissions"
    BOT_PERMISSIONS = "bot_permissions"
    CHANNEL_SUBSCRIBED = "channel_subscribed"
    CHANNEL_NOT_SUBSCRIBED = "channel_not_subscribed"


class SubscriptionStatus(Enum):
    REQUIRED = "required"
    NOT_REQUIRED = "not_required"
    OPTIONAL = "optional"


class CommandValidator:
    def __init__(self, bot: 'Bot') -> None:
        self.bot = bot
        self.data_service = bot.data_service
        self.scheduler_service = bot.scheduler_service

    async def validate_command(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
        checks: Optional[Dict[ValidationCheck, Any]] = None,
    ) -> Tuple[bool, Optional[str], Optional[discord.TextChannel]]:
        channel = target_channel or interaction.channel
        
        if checks is None:
            checks = {
                ValidationCheck.BLACKLIST: True,
                ValidationCheck.USER_PERMISSIONS: True,
                ValidationCheck.BOT_PERMISSIONS: True,
            }
        
        if checks.get(ValidationCheck.BLACKLIST, False):
            is_blacklisted, error_msg = await self._check_blacklist(interaction)
            if is_blacklisted:
                return False, error_msg, channel
        
        if checks.get(ValidationCheck.USER_PERMISSIONS, False):
            has_perms, error_msg = await self._check_user_permissions(interaction)
            if not has_perms:
                return False, error_msg, channel
        
        if checks.get(ValidationCheck.BOT_PERMISSIONS, False):
            has_perms, error_msg = await self._check_bot_permissions(interaction, channel)
            if not has_perms:
                return False, error_msg, channel
        
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)
        is_subscribed = self.scheduler_service.channel_has_active_job(server_id, channel_id)
        
        if ValidationCheck.CHANNEL_SUBSCRIBED in checks:
            config = checks[ValidationCheck.CHANNEL_SUBSCRIBED]
            if not is_subscribed:
                error_msg = self._get_subscription_error_message(
                    channel, 
                    required=True, 
                    custom_message=config if isinstance(config, str) else None
                )
                return False, error_msg, channel
        
        if ValidationCheck.CHANNEL_NOT_SUBSCRIBED in checks:
            config = checks[ValidationCheck.CHANNEL_NOT_SUBSCRIBED]
            if is_subscribed:
                error_msg = self._get_subscription_error_message(
                    channel, 
                    required=False, 
                    custom_message=config if isinstance(config, str) else None
                )
                return False, error_msg, channel
        
        return True, None, channel

    async def _check_blacklist(self, interaction: discord.Interaction) -> Tuple[bool, Optional[str]]:
        server_id = str(interaction.guild.id)
        if await self.data_service.is_blacklisted(server_id):
            return True, "❌ This server has been blacklisted and cannot use this bot."
        return False, None

    async def _check_user_permissions(self, interaction: discord.Interaction) -> Tuple[bool, Optional[str]]:
        member = interaction.guild.get_member(interaction.user.id)
        
        if self.bot.is_owner(interaction.user):
            return True, None
        
        if not member.guild_permissions.manage_messages:
            return False, "❌ You need the `Manage Messages` permission to use this command."
        
        return True, None

    async def _check_bot_permissions(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel
    ) -> Tuple[bool, Optional[str]]:
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
        
        missing_perms = [
            perm.replace('_', ' ').title() 
            for perm, has_perm in required_perms.items() 
            if not has_perm
        ]
        
        if missing_perms:
            return False, f"❌ I'm missing the following permissions in {channel.mention}: {', '.join(missing_perms)}"
        
        return True, None

    def _get_subscription_error_message(
        self, 
        channel: discord.TextChannel, 
        required: bool, 
        custom_message: Optional[str] = None
    ) -> str:
        if custom_message:
            return custom_message.format(channel=channel.mention)
        
        if required:
            return (
                f"❌ {channel.mention} is not subscribed to message deletion.\n"
                f"Use `/subscription add` to set up automatic clearing first."
            )
        else:
            return (
                f"❌ {channel.mention} already has a timer set. "
                f"Use `/subscription update` to update the subscription instead."
            )

    async def send_validation_error(
        self, 
        interaction: discord.Interaction, 
        error_message: str, 
        ephemeral: bool = True
    ) -> None:
        from src.components.validation import ValidationErrorView
        
        view = ValidationErrorView(error_message)
        
        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(view=view, ephemeral=ephemeral)