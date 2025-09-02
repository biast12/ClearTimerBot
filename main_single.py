#!/usr/bin/env python3
"""
Single bot instance runner - handles running a single shard or non-sharded bot
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.bot import ClearTimerBot
from src.core.config import ConfigManager
from src.utils.logger import logger, LogArea


async def run_bot(shard_config=None):
    """Run a single bot instance with optional sharding configuration"""
    # Load configuration first
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Create bot instance with configuration and sharding
    bot = ClearTimerBot(config, shard=shard_config)

    # Run the bot
    try:
        if shard_config:
            logger.info(LogArea.STARTUP, f"Starting bot shard {shard_config[0]}...")
        else:
            logger.info(LogArea.STARTUP, "Starting bot in single-instance mode...")
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


async def main():
    """Main entry point for single bot instance"""
    # Check for sharding environment variables (when called from main.py)
    shard_id = os.environ.get('SHARD_ID')
    shard_count = os.environ.get('SHARD_COUNT')
    
    # Parse sharding configuration
    shard_config = None
    if shard_id is not None and shard_count is not None:
        shard_config = (int(shard_id), int(shard_count))
        logger.info(LogArea.STARTUP, f"Running as shard {shard_id}/{int(shard_count) - 1}")
    
    await run_bot(shard_config)


if __name__ == "__main__":
    # Set up asyncio for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the bot
    asyncio.run(main())