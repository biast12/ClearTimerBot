import pytz
import discord
from datetime import datetime
from utils.bot import initialize_bot
from utils.clear_channel_messages import clear_channel_messages
from utils.command_sync import load_commands, sync_commands, sync_owner_commands
from utils.data_manager import load_servers, load_timezones, load_blacklist, load_env_variables, save_servers
from utils.logger import logger
from utils.notify_missed_clear import notify_missed_clear
from utils.parse_timer import parse_timer
from utils.scheduler import get_scheduler
from utils.version_check import check_for_update

version = "1.0.0"

# Initialize bot
bot = initialize_bot()

# Scheduler for jobs
scheduler = get_scheduler()

# Load environment variables
TOKEN, OWNER_ID, GUILD_ID = load_env_variables()

# Load data
servers = load_servers()
TIMEZONE_ABBREVIATIONS = load_timezones()
blacklist = load_blacklist()

# Event for bot startup
@bot.event
async def on_ready():
    # Check for updates
    check_for_update(version)
    logger.info(f'Logged in as {bot.user}')
    activity = discord.Game(name="Cleaning up the mess! 🧹")
    await bot.change_presence(activity=activity)
    
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
                logger.info(f'Scheduled job {job_id} for server {server_id} and channel {channel_id} with timer {timer} and next run at {next_run_time}')

    try:
        scheduler.start()
        await load_commands(bot)
        await sync_commands(bot)
        if GUILD_ID and OWNER_ID:
            await sync_owner_commands(bot, GUILD_ID)
    except Exception as e:
        logger.error(f'Failed to start bot: {e}')

bot.run(TOKEN)