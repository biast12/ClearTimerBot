import os
import glob
import pytz
import discord
from datetime import datetime
from discord.ext import commands
from utils.clear_channel_messages import clear_channel_messages
from utils.logger import logger
from utils.notify_missed_clear import notify_missed_clear
from utils.parse_timer import parse_timer
from utils.scheduler import get_scheduler
from utils.sync import sync_commands, sync_owner_commands
from utils.utils import get_env_variable, load_servers, load_timezones, load_blacklist, save_servers

# Scheduler for jobs
scheduler = get_scheduler()

# Intents for the bot
intents = discord.Intents.default()
intents.messages = True  # Ensure message intents are enabled
bot = commands.Bot(command_prefix="!", intents=intents)

# Define your Discord bot
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

# Load data
servers = load_servers()
TIMEZONE_ABBREVIATIONS = load_timezones()
blacklist = load_blacklist()

async def load_commands():
    command_files = glob.glob(os.path.join('commands', '*.py'))
    owner_command_files = glob.glob(os.path.join('commands', 'owner', '*.py'))
    all_command_files = command_files + owner_command_files

    for file in all_command_files:
        if os.path.basename(file) == '__init__.py':
            continue
        if 'owner' in file:
            extension = f"commands.owner.{os.path.splitext(os.path.basename(file))[0]}"
        else:
            extension = f"commands.{os.path.splitext(os.path.basename(file))[0]}"
        try:
            await bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}: {e}')

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    activity = discord.Game(name="Cleaning up the mess! 🧹")
    await bot.change_presence(activity=activity)
    
    # Reload jobs from servers.json on startup
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
        await load_commands()
        await sync_commands(bot)
        if GUILD_ID and OWNER_ID:
            await sync_owner_commands(bot, GUILD_ID)
    except Exception as e:
        logger.error(f'Failed to start bot: {e}')

bot.run(TOKEN)