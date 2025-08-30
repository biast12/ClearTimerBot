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
from src.utils.errors import ErrorHandler  # noqa: E402


async def main():
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Create bot instance
    bot = ClearTimerBot(config)

    # Set up error handler
    @bot.tree.error
    async def on_app_command_error(interaction, error):
        await ErrorHandler.handle_command_error(interaction, error)

    # Run the bot
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    # Set up asyncio for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the bot
    asyncio.run(main())
