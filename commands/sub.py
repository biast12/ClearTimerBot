import discord
from discord import app_commands
from discord.ext import commands
from utils.clear_channel_messages import clear_channel_messages
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.logger import logger
from utils.parse_timer import parse_timer
from utils.scheduler import get_scheduler
from utils.data_manager import save_servers, load_servers, load_blacklist

class SubCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sub", description="Subscribe a channel to message deletion")
    @app_commands.checks.has_permissions(manage_messages=True) or is_owner()
    async def sub(self, interaction, timer: str = None, target_channel: discord.TextChannel = None):
        """
        Subscribe a channel to message deletion.

        Args:
            interaction (discord.Interaction): The interaction that triggered the command.
            timer (str): The timer string for scheduling message deletion.
            target_channel (discord.TextChannel, optional): The target channel to subscribe. Defaults to None.
        """
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
            await interaction.response.send_message(f"{channel_mention} already has a timer set. Use `/unsub` to remove it first.", ephemeral=True)
            return
    
        try:
            if timer is None:
                timer = "24h"  # Default to 24-hour interval
            trigger, next_run_time = parse_timer(timer)
    
            # Schedule the job
            scheduler.add_job(clear_channel_messages, trigger, args=[interaction.guild.get_channel(int(channel_id))], id=job_id)
    
            # Save server and channel data with next run time
            if server_id not in servers:
                servers[server_id] = {'server_name': interaction.guild.name, 'channels': {}}
            
            servers[server_id]['channels'][channel_id] = {
                'timer': timer,
                'next_run_time': next_run_time.isoformat()
            }
            save_servers(servers)
    
            # Get Unix timestamp for Discord formatting
            timestamp = int(next_run_time.timestamp())
            next_run_time_full = f"<t:{timestamp}:f>"  # Full date format
            next_run_time_relative = f"<t:{timestamp}:R>"  # Relative format
    
            await interaction.response.send_message(f"Subscribed {channel_mention} to message deletion every {timer}. Next deletion at {next_run_time_full} ({next_run_time_relative}).")
            logger.info(f'Subscribed channel {channel_id} with timer {timer}')
        except ValueError as e:
            await interaction.response.send_message(str(e))
            logger.error(f'Error processing timer: {e}')
        except Exception as e:
            await interaction.response.send_message(f"Error processing timer: {e}")
            logger.error(f'Error processing timer: {e}')

    @sub.error
    async def sub_error(self, interaction, error):
        await handle_error(interaction, error, 'sub')

async def setup(bot):
    await bot.add_cog(SubCommand(bot), override=True)