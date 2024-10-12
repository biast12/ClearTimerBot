import os
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.logger import logger
from utils.scheduler import get_scheduler
from utils.data_manager import load_servers, load_blacklist, save_servers, save_blacklist

class BlacklistAddCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="blacklist_add", description="Blacklist a server from subscribing to message deletion (Bot owner only)")
    @is_owner()
    async def blacklist_add(self, interaction, server_id: str):
        servers = load_servers()
        blacklist = load_blacklist()
        scheduler = get_scheduler()

        server_id = str(server_id)

        channels_unsubscribed = False  # Flag to track if any channels have been unsubscribed
    
        if server_id in blacklist:
            await interaction.response.send_message(f"Server {server_id} is already blacklisted.", ephemeral=True)
            return
    
        if server_id in servers:
            responses = []
            for channel_id in servers[server_id]['channels'].keys():
                job_id = f"{server_id}_{channel_id}"
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
                    channels_unsubscribed = True  # Set flag to True if a channel is unsubscribed
                    # Send notification message in the channel
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        try:
                            await channel.send(f"This channel has been forcefully unsubscribed from message deletion by the bot owner.")
                            responses.append(f"Successfully unsubscribed <#{channel_id}>.")
                        except Exception as e:
                            logger.error(f"Failed to send message in channel {channel_id}: {e}")
                            responses.append(f"Failed to send message in <#{channel_id}>: {e}")
            del servers[server_id]
            save_servers(servers)
    
        blacklist.append(server_id)
        save_blacklist(blacklist)
        
        if channels_unsubscribed:
            await interaction.response.send_message(f"Server {server_id} has been added to the blacklist and all subscriptions removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Server {server_id} has been added to the blacklist.", ephemeral=True)
        
        logger.info(f'Added server {server_id} to blacklist')

    # Error handler for blacklist_add command
    @blacklist_add.error
    async def blacklist_add_error(self, interaction, error):
        await handle_error(interaction, error, 'blacklist_add', True)

async def setup(bot):
    OWNER_ID = os.getenv("OWNER_ID")
    GUILD_ID = os.getenv("GUILD_ID")
    if GUILD_ID and OWNER_ID:
        guild = bot.get_guild(int(GUILD_ID))
        if guild:
            await bot.add_cog(BlacklistAddCommand(bot), guild=guild, override=True)
        else:
            print(f"Guild with ID {GUILD_ID} not found.")
    else:
        print("GUILD_ID not set in environment variables.")