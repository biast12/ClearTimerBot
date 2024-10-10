import logging

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