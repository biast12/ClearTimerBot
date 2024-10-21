import os
import discord
from discord import app_commands

OWNER_ID = os.getenv("OWNER_ID")

if OWNER_ID:
    OWNER_ID = int(OWNER_ID)

# Decorator to check if the user is the owner
def is_owner():
    """
    Check if the user is the owner of the bot.

    Returns:
        commands.check: A check that verifies if the user is the bot owner.
    """
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return False
        return True
    return app_commands.check(predicate)