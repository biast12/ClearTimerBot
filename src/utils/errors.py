import discord
from discord import app_commands
from discord.ext import commands
import traceback
from typing import Union
from src.utils.logger import logger, LogArea


class ErrorHandler:
    @staticmethod
    async def handle_command_error(
        interaction: discord.Interaction,
        error: Union[app_commands.AppCommandError, commands.CommandError],
    ) -> None:
        # Defer if not already responded
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        # Determine error type and message
        if isinstance(error, app_commands.CommandOnCooldown):
            error_title = "⏰ Command on Cooldown"
            error_description = f"Please wait {error.retry_after:.1f} seconds before using this command again."
            error_id = None

        elif isinstance(error, app_commands.MissingPermissions):
            missing = ", ".join(error.missing_permissions)
            error_title = "🔒 Missing Permissions"
            error_description = f"You need the following permissions: {missing}"
            error_id = None

        elif isinstance(error, app_commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            error_title = "🤖 Bot Missing Permissions"
            error_description = f"I need the following permissions: {missing}"
            error_id = None

        elif isinstance(error, app_commands.NoPrivateMessage):
            error_title = "❌ Guild Only"
            error_description = "This command can only be used in a server."
            error_id = None

        elif isinstance(error, app_commands.CheckFailure):
            error_title = "❌ Check Failed"
            error_description = "You don't have permission to use this command."
            error_id = None

        elif isinstance(error, discord.Forbidden):
            error_title = "🚫 Forbidden"
            error_description = "I don't have permission to perform this action."
            error_id = None

        elif isinstance(error, discord.HTTPException):
            error_title = "⚠️ Discord API Error"
            error_description = f"An error occurred with Discord's API: {error.text}"
            error_id = None

        else:
            # Generic error - log it and give user an error ID
            command_name = interaction.command.name if interaction.command else 'Unknown'
            error_id = await logger.log_error(
                LogArea.COMMANDS,
                f"Unhandled error in command: {command_name}",
                exception=error,
                server_id=str(interaction.guild_id) if interaction.guild_id else None,
                channel_id=str(interaction.channel_id) if interaction.channel_id else None,
                user_id=str(interaction.user.id),
                command=command_name
            )
            
            error_title = "❌ An Error Occurred"
            error_description = "An unexpected error occurred. Please report this to the bot owner."

        # Use Components v2 for error display
        from src.components.errors import ErrorView
        
        view = ErrorView(error_title, error_description, error_id)
        
        # Send error message
        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=True)
        else:
            await interaction.response.send_message(view=view, ephemeral=True)
