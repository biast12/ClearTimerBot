import asyncio
import pytz
from utils.logger import logger
from utils.data_manager import load_servers, save_servers

async def clear_channel_messages(channel):
    """
    Clear all messages in the specified Discord channel.

    Args:
        channel (discord.TextChannel): The channel to clear messages from.
    """
    from utils.scheduler import get_scheduler

    servers = load_servers()
    scheduler = get_scheduler()
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
            job_id = f"{server_id}_{channel_id}"
            job = scheduler.get_job(job_id)

            if job:
                next_run_time = job.next_run_time.astimezone(pytz.UTC)  # Convert next_run_time to UTC
                servers[server_id]['channels'][channel_id]['next_run_time'] = next_run_time.isoformat()
                save_servers(servers)
    except Exception as e:
        logger.error(f'Failed to clear messages in channel {channel.id}: {e}')