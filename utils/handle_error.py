from discord import app_commands
from utils.logger import logger

async def handle_error(interaction, error, command_name: str, owner_only=False):
    if isinstance(error, app_commands.CheckFailure):
        if owner_only:
            await interaction.response.send_message("This is a bot owner-only command.", ephemeral=True)
        else:
            await interaction.response.send_message("You do not have the necessary permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred while processing the {command_name} command.", ephemeral=True)
        logger.error(f'Error processing {command_name} command: {error}')