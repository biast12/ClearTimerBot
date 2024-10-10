import os
import discord
from discord import app_commands

OWNER_ID = int(os.getenv("OWNER_ID"))

# Decorator to check if the user is the owner
def is_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return False
        return True
    return app_commands.check(predicate)