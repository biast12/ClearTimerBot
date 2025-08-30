import discord
from discord import app_commands
from discord.ext import commands
import traceback
from typing import Union


class ErrorHandler:
    @staticmethod
    async def handle_command_error(
        interaction: discord.Interaction,
        error: Union[app_commands.AppCommandError, commands.CommandError]
    ) -> None:
        # Defer if not already responded
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(color=discord.Color.red())
        
        # Handle specific error types
        if isinstance(error, app_commands.CommandOnCooldown):
            embed.title = "⏰ Command on Cooldown"
            embed.description = f"Please wait {error.retry_after:.1f} seconds before using this command again."
        
        elif isinstance(error, app_commands.MissingPermissions):
            embed.title = "🔒 Missing Permissions"
            missing = ", ".join(error.missing_permissions)
            embed.description = f"You need the following permissions: {missing}"
        
        elif isinstance(error, app_commands.BotMissingPermissions):
            embed.title = "🤖 Bot Missing Permissions"
            missing = ", ".join(error.missing_permissions)
            embed.description = f"I need the following permissions: {missing}"
        
        elif isinstance(error, app_commands.NoPrivateMessage):
            embed.title = "❌ Guild Only"
            embed.description = "This command can only be used in a server."
        
        elif isinstance(error, app_commands.CheckFailure):
            embed.title = "❌ Check Failed"
            embed.description = "You don't have permission to use this command."
        
        elif isinstance(error, discord.Forbidden):
            embed.title = "🚫 Forbidden"
            embed.description = "I don't have permission to perform this action."
        
        elif isinstance(error, discord.HTTPException):
            embed.title = "⚠️ Discord API Error"
            embed.description = f"An error occurred with Discord's API: {error.text}"
        
        else:
            # Generic error
            embed.title = "❌ An Error Occurred"
            embed.description = str(error)
            
            # Log the full traceback
            print(f"Unhandled error in command: {interaction.command.name if interaction.command else 'Unknown'}")
            traceback.print_exception(type(error), error, error.__traceback__)
        
        # Send error message
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


class BotException(Exception):
    """Base exception for bot-specific errors"""
    pass


class ConfigurationError(BotException):
    """Raised when there's a configuration issue"""
    pass


class DataError(BotException):
    """Raised when there's an issue with data operations"""
    pass


class SchedulerError(BotException):
    """Raised when there's an issue with the scheduler"""
    pass