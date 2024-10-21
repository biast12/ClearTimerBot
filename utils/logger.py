import logging

"""
This module sets up logging for the bot and suppresses logs from the discord library.

Attributes:
    logger (logging.Logger): The logger instance for the bot.
    discord_loggers (list): A list of discord-related loggers to suppress.
"""

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