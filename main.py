#!/usr/bin/env python3
"""
ClearTimer Bot - A Discord bot for automatic message clearing
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.bot import ClearTimerBot  # noqa: E402
from src.core.config import ConfigManager  # noqa: E402
from src.utils.logger import logger, LogArea  # noqa: E402


async def main():
    # Load configuration first
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Create bot instance with configuration
    bot = ClearTimerBot(config)

    # Run the bot
    try:
        logger.info(LogArea.STARTUP, "Starting bot...")
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info(LogArea.STARTUP, "Received shutdown signal (Ctrl+C)")
    except Exception as e:
        error_id = await logger.log_error(
            LogArea.STARTUP,
            "Fatal error occurred during bot operation",
            exception=e
        )
        logger.critical(LogArea.STARTUP, f"Fatal error: {e}. Error ID: {error_id}")
    finally:
        logger.info(LogArea.STARTUP, "Beginning shutdown sequence...")
        await bot.close()
        logger.info(LogArea.STARTUP, "Shutdown complete")


if __name__ == "__main__":
    # Set up asyncio for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the bot
    asyncio.run(main())
