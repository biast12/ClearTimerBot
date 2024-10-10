import os
import discord
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error

class PingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ping', description="Ping the bot")
    async def ping(self, interaction: discord.Interaction):
        latency = self.bot.latency * 1000  # Convert to milliseconds
        await interaction.response.send_message(f'Pong! {latency:.2f} ms', ephemeral=True)

    @ping.error
    async def ping_error(self, interaction: discord.Interaction, error):
        await handle_error(interaction, error, 'ping')

async def setup(bot):
    OWNER_ID = os.getenv("OWNER_ID")
    GUILD_ID = os.getenv("GUILD_ID")
    if GUILD_ID and OWNER_ID:
        guild = bot.get_guild(int(GUILD_ID))
        if guild:
            await bot.add_cog(PingCommand(bot), guild=guild, override=True)
        else:
            print(f"Guild with ID {GUILD_ID} not found.")
    else:
        print("GUILD_ID not set in environment variables.")