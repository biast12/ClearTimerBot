import os
import discord
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.data_manager import load_servers

class ListCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list", description="List all servers and channels subscribed to message deletion (Bot owner only)")
    @is_owner()
    async def list(self, interaction):
        servers = load_servers()
        
        embed = discord.Embed(title="Subscribed Servers and Channels", color=discord.Color.blue())
        
        if not servers:
            embed.description = "No servers or channels are currently subscribed."
        else:
            for server_id, server_data in servers.items():
                server_name = server_data['server_name']
                channels_info = ""
                for channel_id, channel_data in server_data['channels'].items():
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        channels_info += f"{channel.mention} (Timer: {channel_data['timer']})\n"
                embed.add_field(name=f"{server_name} (ID: {server_id})", value=channels_info or "No channels subscribed", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Error handler for list command
    @list.error
    async def list_error(self, interaction, error):
        await handle_error(interaction, error, 'list', True)

async def setup(bot):
    OWNER_ID = os.getenv("OWNER_ID")
    GUILD_ID = os.getenv("GUILD_ID")
    if GUILD_ID and OWNER_ID:
        guild = bot.get_guild(int(GUILD_ID))
        if guild:
            await bot.add_cog(ListCommand(bot), guild=guild, override=True)
        else:
            print(f"Guild with ID {GUILD_ID} not found.")
    else:
        print("GUILD_ID not set in environment variables.")