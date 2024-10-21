import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from utils.clear_channel_messages import clear_channel_messages
from utils.data_manager import load_servers, save_servers
from utils.logger import logger
from utils.notify_missed_clear import notify_missed_clear
from utils.parse_timer import parse_timer

# Scheduler for jobs
scheduler = AsyncIOScheduler()

def get_scheduler():
    """
    Get an instance of the AsyncIOScheduler.

    Returns:
        AsyncIOScheduler: The scheduler instance.
    """
    return scheduler

async def schedule_jobs(bot):
    """
    Schedule jobs for all channels based on the loaded server data.

    Args:
        bot (commands.Bot): The bot instance.
    """
    servers = load_servers()
    if servers:
        for server_id, server_data in servers.items():
            for channel_id, channel_data in server_data['channels'].items():
                await schedule_job(bot, servers, server_id, channel_id, channel_data)

async def schedule_job(bot, servers, server_id, channel_id, channel_data):
    """
    Schedule a job for a specific channel.

    Args:
        bot (commands.Bot): The bot instance.
        servers (dict): The server data.
        server_id (str): The ID of the server.
        channel_id (str): The ID of the channel.
        channel_data (dict): The data for the channel.
    """
    timer = channel_data['timer']
    next_run_time = datetime.fromisoformat(channel_data['next_run_time'])
    channel = bot.get_channel(int(channel_id))
    job_id = f"{server_id}_{channel_id}"

    if next_run_time < datetime.now(pytz.UTC):
        logger.info(f'Adjusting next_run_time for channel {channel_id} as it is in the past.')
        trigger, next_run_time = parse_timer(timer)
        servers[server_id]['channels'][channel_id]['next_run_time'] = next_run_time.isoformat()
        save_servers(servers)
        await notify_missed_clear(channel, job_id)
    else:
        trigger, _ = parse_timer(timer)

    scheduler.add_job(clear_channel_messages, trigger, args=[channel], id=job_id, next_run_time=next_run_time)
    logger.info(f'Scheduled job {job_id} for server {server_id} and channel {channel_id} with timer {timer} and next run at {next_run_time}')