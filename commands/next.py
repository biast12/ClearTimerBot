import discord
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.scheduler import get_scheduler
from utils.utils import load_blacklist

class NextCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="next", description="Check when the next message clear is scheduled")
    async def next(self, interaction, target_channel: discord.TextChannel = None):
        blacklist = load_blacklist()
        scheduler = get_scheduler()

        server_id = str(interaction.guild.id)
        channel_id = str((target_channel or interaction.channel).id)
        channel_mention = str((target_channel or interaction.channel).mention)
        job_id = f"{server_id}_{channel_id}"
    
        if server_id in blacklist:
            await interaction.response.send_message(f"Server {server_id} is blacklisted and cannot use commands from this bot", ephemeral=True)
            return
    
        # Check if there's a job scheduled for this channel
        job = scheduler.get_job(job_id)
        if job:
            next_run = job.next_run_time  # This is a datetime object
            if next_run:
                # Convert next_run to a Unix timestamp for Discord's relative timestamp formatting
                timestamp = int(next_run.timestamp())
                next_run_time_full = f"<t:{timestamp}:f>"  # Full date format
                next_run_time_relative = f"<t:{timestamp}:R>"  # Relative format
    
                await interaction.response.send_message(
                    f"The next message clear for {channel_mention} is scheduled at {next_run_time_full} ({next_run_time_relative})."
                )
            else:
                await interaction.response.send_message(f"No upcoming runs found for {channel_mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No timer is set for {channel_mention}. Use `/sub` to set a timer.", ephemeral=True)

    @next.error
    async def next_error(self, interaction, error):
        await handle_error(interaction, error, 'next')

async def setup(bot):
    await bot.add_cog(NextCommand(bot), override=True)