import os
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.logger import logger
from utils.scheduler import get_scheduler
from utils.data_manager import load_servers, save_servers

class ForceUnsubCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="force_unsub", description="Force unsubscribe a server or channel from message deletion (Bot owner only)")
    @is_owner()
    async def force_unsub(self, interaction, target_id: str):
        servers = load_servers()
        scheduler = get_scheduler()

        target_id = str(target_id)
    
        if target_id.isdigit() and target_id in servers:
            # target_id is a server ID
            responses = []
            for channel_id in servers[target_id]['channels'].keys():
                job_id = f"{target_id}_{channel_id}"
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
                    # Send notification message in the channel
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        try:
                            await channel.send(f"This channel has been forcefully unsubscribed from message deletion by the bot owner.")
                            responses.append(f"Successfully unsubscribed <#{channel_id}>.")
                        except Exception as e:
                            logger.error(f"Failed to send message in channel {channel_id}: {e}")
                            responses.append(f"Failed to send message in <#{channel_id}>: {e}")
            del servers[target_id]
            save_servers(servers)
            await interaction.response.send_message("\n".join(responses), ephemeral=True)
            logger.info(f'Forcefully unsubscribed all channels in server {target_id}')
        elif target_id.isdigit():
            # Check if target_id is a channel ID in any server
            found = False
            for server_id, server_data in servers.items():
                if target_id in server_data['channels']:
                    found = True
                    job_id = f"{server_id}_{target_id}"
                    if scheduler.get_job(job_id):
                        scheduler.remove_job(job_id)
                        del server_data['channels'][target_id]
                        if not server_data['channels']:
                            del servers[server_id]  # Remove server if no channels left
                        save_servers(servers)
                    # Send notification message in the channel
                    channel = self.bot.get_channel(int(target_id))
                    if channel:
                        try:
                            await channel.send(f"This channel has been forcefully unsubscribed from message deletion by the bot owner.")
                            await interaction.response.send_message(f"Forcefully unsubscribed <#{target_id}> from message deletion in server {server_id}.", ephemeral=True)
                        except Exception as e:
                            logger.error(f"Failed to send message in channel {target_id}: {e}")
                            await interaction.response.send_message(f"Forcefully unsubscribed <#{target_id}> from message deletion in server {server_id}, but failed to send notification: {e}", ephemeral=True)
                    logger.info(f'Forcefully unsubscribed channel {target_id} in server {server_id}')
                    break
            if not found:
                await interaction.response.send_message("Invalid server ID or channel ID.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid server ID or channel ID.", ephemeral=True)

    # Error handler for force_unsub command
    @force_unsub.error
    async def force_unsub_error(self, interaction, error):
        await handle_error(interaction, error, 'force_unsub', True)

async def setup(bot):
    OWNER_ID = os.getenv("OWNER_ID")
    GUILD_ID = os.getenv("GUILD_ID")
    if GUILD_ID and OWNER_ID:
        guild = bot.get_guild(int(GUILD_ID))
        if guild:
            await bot.add_cog(ForceUnsubCommand(bot), guild=guild, override=True)
        else:
            print(f"Guild with ID {GUILD_ID} not found.")
    else:
        print("GUILD_ID not set in environment variables.")