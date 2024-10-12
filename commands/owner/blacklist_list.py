import os
import discord
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.data_manager import load_blacklist

class BlacklistListCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='blacklist_list', description="List all blacklisted servers (Bot owner only)")
    @is_owner()
    async def blacklist_list(self, interaction):
        blacklist = load_blacklist()

        embed = discord.Embed(
            title="Blacklisted Servers",
            color=0xFF0000,  # Red color in hexadecimal
        )
    
        if not blacklist:
            embed.description = "No servers are currently blacklisted."
        else:
            for server_id in blacklist:
                server = self.bot.get_guild(int(server_id))
                server_name = server.name if server else "Unknown Server"
                embed.add_field(name=f"{server_name} (ID: {server_id})", value="\u200b", inline=False)
    
        embed.timestamp = discord.utils.utcnow()
    
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Error handler for blacklist_list command
    @blacklist_list.error
    async def blacklist_list_error(self, interaction, error):
        await handle_error(interaction, error, 'blacklist_list', True)

async def setup(bot):
    OWNER_ID = os.getenv("OWNER_ID")
    GUILD_ID = os.getenv("GUILD_ID")
    if GUILD_ID and OWNER_ID:
        guild = bot.get_guild(int(GUILD_ID))
        if guild:
            await bot.add_cog(BlacklistListCommand(bot), guild=guild, override=True)
        else:
            print(f"Guild with ID {GUILD_ID} not found.")
    else:
        print("GUILD_ID not set in environment variables.")