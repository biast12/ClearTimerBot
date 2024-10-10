import discord
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.logger import logger
from utils.scheduler import get_scheduler
from utils.utils import load_servers, load_blacklist, save_servers

class UnsubCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unsub", description="Unsubscribe from message deletion")
    @app_commands.checks.has_permissions(manage_messages=True) or is_owner()
    async def unsub(self, interaction, target_channel: discord.TextChannel = None):
        servers = load_servers()
        blacklist = load_blacklist()
        scheduler = get_scheduler()
        
        server_id = str(interaction.guild.id)
        channel_id = str((target_channel or interaction.channel).id)
        channel_mention = str((target_channel or interaction.channel).mention)
        job_id = f"{server_id}_{channel_id}"
    
        if server_id in blacklist:
            await interaction.response.send_message(f"Server {server_id} is blacklisted and cannot use commands from this bot", ephemeral=True)
            return
    
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            if channel_id in servers.get(server_id, {}).get('channels', {}):
                del servers[server_id]['channels'][channel_id]
                if not servers[server_id]['channels']:
                    del servers[server_id]  # Remove server if no channels left
                save_servers(servers)
            await interaction.response.send_message(f"Unsubscribed {channel_mention} from message deletion.")
            logger.info(f'Unsubscribed channel {channel_id}')
        else:
            await interaction.response.send_message("This channel is not subscribed.", ephemeral=True)

    @unsub.error
    async def unsub_error(self, interaction, error):
        await handle_error(interaction, error, 'unsub')

async def setup(bot):
    await bot.add_cog(UnsubCommand(bot), override=True)