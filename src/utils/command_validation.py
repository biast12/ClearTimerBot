import discord
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING
from enum import Enum
from src.localization import get_translator
from src.utils.logger import logger, LogArea

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
    def __init__(self, bot: "Bot") -> None:
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

        if ValidationCheck.USER_PERMISSIONS in checks:
            permission_config = checks[ValidationCheck.USER_PERMISSIONS]
            has_perms, error_msg = await self._check_user_permissions(
                interaction, permission_config
            )
            if not has_perms:
                return False, error_msg, channel

        if checks.get(ValidationCheck.BOT_PERMISSIONS, False):
            has_perms, error_msg = await self._check_bot_permissions(
                interaction, channel
            )
            if not has_perms:
                return False, error_msg, channel

        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check both scheduler AND database for subscription status
        # This prevents race conditions where data is saved but job isn't created yet
        has_scheduler_job = self.scheduler_service.channel_has_active_job(
            server_id, channel_id
        )

        # Also check database for subscription
        server = await self.data_service.get_server(server_id)
        has_database_entry = (
            server and channel_id in server.channels if server else False
        )

        # Channel is considered subscribed if it exists in either scheduler OR database
        is_subscribed = has_scheduler_job or has_database_entry

        if ValidationCheck.CHANNEL_SUBSCRIBED in checks:
            config = checks[ValidationCheck.CHANNEL_SUBSCRIBED]
            if not is_subscribed:
                error_msg = await self._get_subscription_error_message(
                    interaction,
                    channel,
                    required=True,
                    custom_message=config if isinstance(config, str) else None,
                )
                return False, error_msg, channel

        if ValidationCheck.CHANNEL_NOT_SUBSCRIBED in checks:
            config = checks[ValidationCheck.CHANNEL_NOT_SUBSCRIBED]
            if is_subscribed:
                error_msg = await self._get_subscription_error_message(
                    interaction,
                    channel,
                    required=False,
                    custom_message=config if isinstance(config, str) else None,
                )
                return False, error_msg, channel

        return True, None, channel

    async def _check_blacklist(
        self, interaction: discord.Interaction
    ) -> Tuple[bool, Optional[str]]:
        server_id = str(interaction.guild.id)
        if await self.data_service.is_blacklisted(server_id):
            translator = await get_translator(server_id, self.data_service)
            return True, translator.get("validation.blacklisted")
        return False, None

    async def _check_user_permissions(
        self, interaction: discord.Interaction, permission_config: Any = None
    ) -> Tuple[bool, Optional[str]]:
        if isinstance(interaction.user, discord.Member):
            member = interaction.user
        else:
            member = interaction.guild.get_member(interaction.user.id)

        if not member:
            server_id = str(interaction.guild.id)
            translator = await get_translator(server_id, self.data_service)
            return False, translator.get("validation.insufficient_permissions")

        if self.bot.is_owner(interaction.user):
            return True, None

        # Determine which permission to check
        if permission_config is True or permission_config is None:
            # Default to manage_messages for backward compatibility
            required_permission = "manage_messages"
        elif isinstance(permission_config, str):
            # Use the specified permission
            required_permission = permission_config
        else:
            # Default to manage_messages
            required_permission = "manage_messages"

        # Check if the member has the required permission
        has_permission = getattr(member.guild_permissions, required_permission, False)

        if not has_permission:
            server_id = str(interaction.guild.id)
            translator = await get_translator(server_id, self.data_service)
            return False, translator.get("validation.insufficient_permissions")

        return True, None

    async def _check_bot_permissions(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ) -> Tuple[bool, Optional[str]]:
        bot_permissions = channel.permissions_for(interaction.guild.me)

        required_perms = {
            "view_channel": bot_permissions.view_channel,
            "send_messages": bot_permissions.send_messages,
            "read_message_history": bot_permissions.read_message_history,
            "manage_messages": bot_permissions.manage_messages,
            "embed_links": bot_permissions.embed_links,
            "use_application_commands": bot_permissions.use_application_commands,
            "send_messages_in_threads": bot_permissions.send_messages_in_threads,
        }

        missing_perms = [
            perm.replace("_", " ").title()
            for perm, has_perm in required_perms.items()
            if not has_perm
        ]

        if missing_perms:
            server_id = str(interaction.guild.id)
            translator = await get_translator(server_id, self.data_service)
            perms_list = ", ".join(missing_perms)
            return False, translator.get(
                "validation.bot_missing_permissions",
                channel=channel.mention,
                permissions=perms_list,
            )

        return True, None

    async def _get_subscription_error_message(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        required: bool,
        custom_message: Optional[str] = None,
    ) -> str:
        if custom_message:
            return custom_message.format(channel=channel.mention)

        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)

        if required:
            return translator.get("validation.not_subscribed", channel=channel.mention)
        else:
            return translator.get(
                "validation.channel_already_subscribed", channel=channel.mention
            )

    async def send_validation_error(
        self,
        interaction: discord.Interaction,
        error_message: str,
        ephemeral: bool = True,
    ) -> None:
        from src.components.validation import ValidationErrorView

        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        view = ValidationErrorView(error_message, translator)

        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(view=view, ephemeral=ephemeral)
