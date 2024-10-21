import discord
from utils.bot import initialize_bot
from utils.command_sync import load_commands, sync_commands, sync_owner_commands
from utils.data_manager import load_env_variables
from utils.handle_error import handle_error
from utils.logger import logger
from utils.scheduler import get_scheduler, schedule_jobs
from utils.version_check import check_for_update

version = "1.0.1"

# Initialize bot
bot = initialize_bot()

# Scheduler for jobs
scheduler = get_scheduler()

# Load environment variables
TOKEN, OWNER_ID, GUILD_ID = load_env_variables()

# Event for bot startup
@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready.
    """
    try:
        check_for_update(version)
        logger.info(f'Logged in as {bot.user}')
        activity = discord.Game(name="Cleaning up the mess! 🧹")
        await bot.change_presence(activity=activity)
        
        await schedule_jobs(bot)

        scheduler.start()
        await load_commands(bot)
        await sync_commands(bot)
        if GUILD_ID and OWNER_ID:
            await sync_owner_commands(bot, GUILD_ID)
    except discord.DiscordException as e:
        logger.error(f'Discord error: {e}')
    except Exception as e:
        logger.error(f'Unexpected error: {e}')

# Handle errors
@bot.event
async def on_command_error(ctx, error):
    await handle_error(ctx, error)

bot.run(TOKEN)