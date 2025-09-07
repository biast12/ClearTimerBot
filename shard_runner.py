#!/usr/bin/env python3
"""
Shard runner - handles running a single shard of the bot
"""

import asyncio
import sys
import os
from pathlib import Path
import io

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    # Set console code page to UTF-8
    os.system("chcp 65001 >nul 2>&1")

sys.path.insert(0, str(Path(__file__).parent))

from src.core.bot import ClearTimerBot
from src.core.config import ConfigManager
from src.utils.logger import logger, LogArea


async def run_shard():
    """Run a single shard based on environment variables"""
    shard_id = int(os.environ.get("SHARD_ID", 0))
    shard_count = int(os.environ.get("SHARD_COUNT", 1))
    config_manager = ConfigManager()
    config = config_manager.load_config()
    bot = ClearTimerBot(config, shard=(shard_id, shard_count))
    bot.restart_requested = False

    try:
        logger.info(
            LogArea.STARTUP, f"Starting bot shard {shard_id}/{shard_count - 1}..."
        )
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info(LogArea.STARTUP, "Received shutdown signal")
    except Exception as e:
        if not isinstance(e, SystemExit):
            error_id = await logger.log_error(
                LogArea.STARTUP, f"Fatal error in shard {shard_id}", exception=e
            )
            logger.critical(LogArea.STARTUP, f"Fatal error: {e}. Error ID: {error_id}")
            raise
    finally:
        await bot.close()
        if hasattr(bot, "restart_requested") and bot.restart_requested:
            sys.exit(99)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_shard())
