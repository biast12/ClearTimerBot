import os
import re
import json
import pytz
import discord
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from discord.app_commands import MissingPermissions
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Setup logging
logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S', format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Suppress all discord logs
discord_loggers = [
    'discord',
    'discord.gateway',
    'discord.client',
    'discord.ext.commands',
    'discord.ext.commands.bot',
]

for logger_name in discord_loggers:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Intents for the bot
intents = discord.Intents.default()
intents.messages = True  # Ensure message intents are enabled
bot = commands.Bot(command_prefix="!", intents=intents)

# Scheduler for jobs
scheduler = AsyncIOScheduler()

# First-time installation check
env_path = Path('.env')
if not env_path.is_file():
    env_path.touch()

load_dotenv(dotenv_path=env_path)

def get_env_variable(var_name, prompt_message):
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    value = os.getenv(var_name)
    if value is None:
        value = input(prompt_message)
        with open(env_path, 'a') as f:
            f.write(f"{var_name}={value}\n")
        load_dotenv(dotenv_path=env_path)
        value = os.getenv(var_name)
    return value

# Define your Discord bot token
TOKEN = get_env_variable('DISCORD_BOT_TOKEN', "Please enter your Discord bot token: ")

# Define your user ID
OWNER_ID = get_env_variable('OWNER_ID', "Please enter your User ID (for owner only commands) (can leave blank): ")

# Convert OWNER_ID to integer if it's set
if OWNER_ID:
    OWNER_ID = int(OWNER_ID)

# Define your test server ID
GUILD_ID = get_env_variable('GUILD_ID', "Please enter your test server ID (for owner only commands) (can leave blank): ")

# Convert GUILD_ID to integer if it's set
if GUILD_ID:
    GUILD_ID = int(GUILD_ID)

# File paths and constants
DATA_FILE = 'data.json'
TIMEZONE_FILE = 'timezone_abbreviations.json'

# Ensure data.json exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

# Load or initialize server data
def load_servers():
    if os.path.exists(DATA_FILE) and os.stat(DATA_FILE).st_size > 0:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Load timezone abbreviations from the external file
def load_timezones():
    with open(TIMEZONE_FILE, 'r') as f:
        return json.load(f)

# Save server data
def save_servers(servers):
    with open(DATA_FILE, 'w') as f:
        json.dump(servers, f, indent=4)

servers = load_servers()
TIMEZONE_ABBREVIATIONS = load_timezones()

# Get the full timezone name from the abbreviation.
def get_timezone(timezone_abbr):
    timezone_str = TIMEZONE_ABBREVIATIONS.get(timezone_abbr)
    if not timezone_str:
        raise ValueError(f"Unknown timezone abbreviation: {timezone_abbr}")
    return pytz.timezone(timezone_str)

# Parse the timer string and return the appropriate trigger and next run time.
def parse_timer(timer):
    timezone_pattern = r'(\d{1,2}:\d{2})\s*([A-Z]*)'  # Matches "<time> <timezone>" with optional timezone
    timezone_matches = re.match(timezone_pattern, timer)

    if timezone_matches:
        time_str = timezone_matches.group(1)
        timezone_abbr = timezone_matches.group(2) or 'GMT'  # Default to GMT if no timezone is provided
        hour, minute = map(int, time_str.split(':'))
        timezone = get_timezone(timezone_abbr)
        next_run_time = datetime.now(timezone).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run_time < datetime.now(timezone):  # Adjust if the time is in the past today
            next_run_time += timedelta(days=1)
        trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)
    else:
        pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?'
        matches = re.match(pattern, timer)
        if matches:
            days = int(matches.group(1) or 0)
            hours = int(matches.group(2) or 0)
            minutes = int(matches.group(3) or 0)
            delta = timedelta(days=days, hours=hours, minutes=minutes)
            next_run_time = datetime.now(pytz.UTC) + delta
            total_minutes = (days * 24 * 60) + (hours * 60) + minutes
            trigger = IntervalTrigger(minutes=total_minutes)
        else:
            raise ValueError("Invalid timer format. Use '1d2h3m' or 'HH:MM <timezone>' format for durations.")
    return trigger, next_run_time

# Decorator to check if the user is the owner
def is_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return False
        return True
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')

    # Set funny Rich Presence
    activity = discord.Game(name="Cleaning up the mess! 🧹")
    await bot.change_presence(activity=activity)

    # Reload jobs from data.json on startup
    if servers:
        for server_id, server_data in servers.items():
            for channel_id, channel_data in server_data['channels'].items():
                timer = channel_data['timer']
                next_run_time = datetime.fromisoformat(channel_data['next_run_time'])
                channel = bot.get_channel(int(channel_id))
                job_id = f"{server_id}_{channel_id}"

                # If the next_run_time is in the past, adjust it and notify the channel
                if next_run_time < datetime.now(pytz.UTC):
                    logger.info(f'Adjusting next_run_time for channel {channel_id} as it is in the past.')
                    trigger, next_run_time = parse_timer(timer)
                    servers[server_id]['channels'][channel_id]['next_run_time'] = next_run_time.isoformat()
                    save_servers(servers)
                    
                    # Notify the channel and provide buttons for user action
                    await notify_missed_clear(channel, job_id)
                else:
                    # Use the stored next_run_time to continue from where the bot left off
                    trigger, _ = parse_timer(timer)

                # Schedule the job with the existing or adjusted next_run_time
                scheduler.add_job(clear_channel_messages, trigger, args=[channel], id=job_id, next_run_time=next_run_time)
                logger.info(f'Scheduled job {job_id} with timer {timer} and next run at {next_run_time}')

    try:
        scheduler.start()
        # Sync commands globally
        bot.tree.clear_commands(guild=None)
        bot.tree.add_command(cleartimer_sub)
        bot.tree.add_command(cleartimer_unsub)
        bot.tree.add_command(cleartimer_next)
        bot.tree.add_command(help_command)
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} commands globally')

        # Sync bot owner commands for the bot owner's guild
        if OWNER_ID and GUILD_ID:
            bot_owner_guild = bot.get_guild(GUILD_ID)
            if bot_owner_guild:
                bot.tree.clear_commands(guild=bot_owner_guild)
                bot.tree.add_command(cleartimer_list, guild=bot_owner_guild)
                synced_owner = await bot.tree.sync(guild=bot_owner_guild)
                logger.info(f'Synced {len(synced_owner)} commands for bot owner\'s guild')

    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

async def notify_missed_clear(channel, job_id):
    class ClearChannelView(discord.ui.View):
        def __init__(self, job_id):
            super().__init__(timeout=60)  # Timeout after 60 seconds
            self.job_id = job_id

        @discord.ui.button(label="Yes, clear the channel messages now", style=discord.ButtonStyle.danger)
        async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message("You do not have permission to manage messages.", ephemeral=True)
                return
            await interaction.response.defer()  # Defer the interaction response
            await clear_channel_messages(channel)
            await interaction.followup.send("Channel messages have been cleared.", ephemeral=True)
            self.stop()

        @discord.ui.button(label="No, do not clear the channel messages now", style=discord.ButtonStyle.secondary)
        async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message("You do not have permission to manage messages.", ephemeral=True)
                return
            await interaction.response.defer()  # Defer the interaction response
            await interaction.followup.send("Channel messages will not be cleared.", ephemeral=True)
            await interaction.message.delete()  # Delete the original message
            self.stop()

    await channel.send(
        "The bot was down when it should have cleared the channel messages. Would you like to clear the messages now?",
        view=ClearChannelView(job_id)
    )

# Command: Subscribe to message deletion
@bot.tree.command(name="cleartimer_sub", description="Subscribe a channel to message deletion")
@app_commands.checks.has_permissions(manage_messages=True)
async def cleartimer_sub(ctx, timer: str = None, target_channel: discord.TextChannel = None):
    server_id = str(ctx.guild.id)
    channel_id = str((target_channel or ctx.channel).id)
    channel_mention = str((target_channel or ctx.channel).mention)
    job_id = f"{server_id}_{channel_id}"

    if scheduler.get_job(job_id):
        await ctx.response.send_message(f"{channel_mention} already has a timer set. Use `/cleartimer_unsub` to remove it first.", ephemeral=True)
        return

    try:
        if timer is None:
            timer = "24h"  # Default to 24-hour interval
        trigger, next_run_time = parse_timer(timer)

        # Schedule the job
        scheduler.add_job(clear_channel_messages, trigger, args=[ctx.guild.get_channel(int(channel_id))], id=job_id)

        # Save server and channel data with next run time
        if server_id not in servers:
            servers[server_id] = {'server_name': ctx.guild.name, 'channels': {}}
        
        servers[server_id]['channels'][channel_id] = {
            'timer': timer,
            'next_run_time': next_run_time.isoformat()
        }
        save_servers(servers)

        # Get Unix timestamp for Discord formatting
        timestamp = int(next_run_time.timestamp())
        next_run_time_full = f"<t:{timestamp}:f>"  # Full date format
        next_run_time_relative = f"<t:{timestamp}:R>"  # Relative format

        await ctx.response.send_message(f"Subscribed {channel_mention} to message deletion every {timer}. Next deletion at {next_run_time_full} ({next_run_time_relative}).")
        logger.info(f'Subscribed channel {channel_id} with timer {timer}')
    except ValueError as e:
        await ctx.response.send_message(str(e))
        logger.error(f'Error processing timer: {e}')
    except Exception as e:
        await ctx.response.send_message(f"Error processing timer: {e}")
        logger.error(f'Error processing timer: {e}')

# Error handler for MissingPermissions
@cleartimer_sub.error
async def cleartimer_sub_error(ctx, error):
    if isinstance(error, MissingPermissions):
        # Send an ephemeral message if the user lacks the required permission
        await ctx.response.send_message("You do not have the necessary permission to manage messages.", ephemeral=True)

# Command: Unsubscribe from message deletion
@bot.tree.command(name="cleartimer_unsub", description="Unsubscribe from message deletion")
@app_commands.checks.has_permissions(manage_messages=True)
async def cleartimer_unsub(ctx, target_channel: discord.TextChannel = None):
    server_id = str(ctx.guild.id)
    channel_id = str((target_channel or ctx.channel).id)
    channel_mention = str((target_channel or ctx.channel).mention)
    job_id = f"{server_id}_{channel_id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        if channel_id in servers.get(server_id, {}).get('channels', {}):
            del servers[server_id]['channels'][channel_id]
            if not servers[server_id]['channels']:
                del servers[server_id]  # Remove server if no channels left
            save_servers(servers)
        await ctx.response.send_message(f"Unsubscribed {channel_mention} from message deletion.")
        logger.info(f'Unsubscribed channel {channel_id}')
    else:
        await ctx.response.send_message("This channel is not subscribed.", ephemeral=True)

# Error handler for cleartimer_unsub
@cleartimer_unsub.error
async def cleartimer_unsub_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.response.send_message("You do not have the necessary permission to manage messages.", ephemeral=True)

# Command: Print next run time for a channel
@bot.tree.command(name="cleartimer_next", description="Check when the next message clear is scheduled")
async def cleartimer_next(ctx, target_channel: discord.TextChannel = None):
    server_id = str(ctx.guild.id)
    channel_id = str((target_channel or ctx.channel).id)
    channel_mention = str((target_channel or ctx.channel).mention)
    job_id = f"{server_id}_{channel_id}"

    # Check if there's a job scheduled for this channel
    job = scheduler.get_job(job_id)
    if job:
        next_run = job.next_run_time  # This is a datetime object
        if next_run:
            # Convert next_run to a Unix timestamp for Discord's relative timestamp formatting
            timestamp = int(next_run.timestamp())
            next_run_time_full = f"<t:{timestamp}:f>"  # Full date format
            next_run_time_relative = f"<t:{timestamp}:R>"  # Relative format

            await ctx.response.send_message(
                f"The next message clear for {channel_mention} is scheduled at {next_run_time_full} ({next_run_time_relative})."
            )
        else:
            await ctx.response.send_message(f"No upcoming runs found for {channel_mention}.", ephemeral=True)
    else:
        await ctx.response.send_message(f"No timer is set for {channel_mention}. Use `/cleartimer_sub` to set a timer.", ephemeral=True)

# Command: Help command
@bot.tree.command(name="help", description="Display available commands and help server link")
async def help_command(ctx):
    help_message = (
        " **Available Commands:**\n"
        "`/cleartimer_sub [timer] [target_channel]` - Subscribe a channel to message deletion\n"
        "- Timer syntax: `1d2h3m` for days, hours, and minutes or `HH:MM <timezone>` for specific times every day\n\n"
        "`/cleartimer_unsub [target_channel]` - Unsubscribe from message deletion\n"
        "`/cleartimer_next [target_channel]` - Check when the next message clear is scheduled\n\n"
        "For more help, join our help server: [Help Server](https://discord.com/invite/ERFffj9Qs7)"
    )
    await ctx.response.send_message(help_message)

# Command: List all servers and channels subscribed to message deletion (Bot owner only)
@bot.tree.command(name="cleartimer_list", description="List all servers and channels subscribed to message deletion (Bot owner only)")
@is_owner()
async def cleartimer_list(ctx):
    embed = discord.Embed(title="Subscribed Servers and Channels", color=discord.Color.blue())
    
    if not servers:
        embed.description = "No servers or channels are currently subscribed."
    else:
        for server_id, server_data in servers.items():
            server_name = server_data['server_name']
            channels_info = ""
            for channel_id, channel_data in server_data['channels'].items():
                channel = bot.get_channel(int(channel_id))
                if channel:
                    channels_info += f"{channel.mention} (Timer: {channel_data['timer']})\n"
            embed.add_field(name=f"{server_name} (ID: {server_id})", value=channels_info or "No channels subscribed", inline=False)
    
    await ctx.response.send_message(embed=embed, ephemeral=True)

# Error handler for cleartimer_list command
@cleartimer_list.error
async def cleartimer_list_error(ctx, error):
    if isinstance(error, app_commands.CheckFailure):
        await ctx.response.send_message("This is a bot owner-only command.", ephemeral=True)
    else:
        await ctx.response.send_message("An error occurred while processing the command.", ephemeral=True)

# Function: Clear messages in the channel and update next_run_time
async def clear_channel_messages(channel):
    logger.info(f'Attempting to clear messages in channel {channel.id}')

    permissions = channel.permissions_for(channel.guild.me)
    if not permissions.manage_messages or not permissions.read_message_history:
        logger.error(f'Missing necessary permissions in channel {channel.id}')
        return

    try:
        async for message in channel.history():
            await message.delete()
            await asyncio.sleep(1)  # Add delay to avoid rate limits
        logger.info(f'Cleared messages in channel {channel.id}')

        # Update next_run_time after clearing messages
        server_id = str(channel.guild.id)
        channel_id = str(channel.id)

        if server_id in servers and channel_id in servers[server_id]['channels']:
            # Get the scheduled job for this channel
            job_id = f"{server_id}_{channel_id}"
            job = scheduler.get_job(job_id)

            if job:
                next_run_time = job.next_run_time.astimezone(pytz.UTC)  # Convert next_run_time to UTC
                servers[server_id]['channels'][channel_id]['next_run_time'] = next_run_time.isoformat()

                # Save the updated next_run_time
                save_servers(servers)
    except Exception as e:
        logger.error(f'Failed to clear messages in channel {channel.id}: {e}')

bot.run(TOKEN)