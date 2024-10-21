from discord import app_commands
from utils.logger import logger

async def handle_error(interaction, error, command_name: str, owner_only=False):
    """
    Handle errors that occur during command execution.

    Args:
        interaction (discord.Interaction): The interaction that triggered the error.
        error (Exception): The error that occurred.
        command_name (str): The name of the command that caused the error.
        owner_only (bool): Whether the command is bot owner-only.
    """
    if isinstance(error, app_commands.CheckFailure):
        if owner_only:
            await interaction.response.send_message("This is a bot owner-only command.", ephemeral=True)
        else:
            await interaction.response.send_message("You do not have the necessary permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred while processing the {command_name} command.", ephemeral=True)
        logger.error(f'Error processing {command_name} command: {error}')