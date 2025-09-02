#!/usr/bin/env python3
"""
Command Registration Script - Registers slash commands with Discord
"""

import asyncio
import sys
from pathlib import Path
import argparse
import discord
from discord.ext import commands

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import ConfigManager
from src.utils.logger import logger, LogArea


# Mock classes for command registration
class MockScheduleParser:
    """Mock schedule parser for command registration"""

    pass


class MockSchedulerService:
    """Mock scheduler service for command registration"""

    def __init__(self):
        self.schedule_parser = MockScheduleParser()


class MockDataService:
    """Mock data service for command registration"""

    pass


class MockMessageService:
    """Mock message service for command registration"""

    pass


class CommandRegisterBot(commands.Bot):
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

        self.config = config
        # Mock services that commands expect
        self.data_service = MockDataService()
        self.scheduler_service = MockSchedulerService()
        self.message_service = MockMessageService()

    async def setup_hook(self):
        # Load command cogs
        command_modules = [
            "src.commands.subscription",
            "src.commands.general",
        ]

        for module in command_modules:
            try:
                await self.load_extension(module)
                logger.info(LogArea.NONE, f"Loaded extension: {module}")
            except Exception as e:
                logger.error(LogArea.NONE, f"Failed to load extension {module}: {e}")

        # Load admin commands if GUILD_ID is configured
        if self.config.guild_id:
            try:
                await self.load_extension("src.commands.admin")
                logger.info(LogArea.NONE, "Loaded extension: src.commands.admin")
            except Exception as e:
                logger.error(LogArea.NONE, f"Failed to load admin commands: {e}")
        
        # Load owner commands if both OWNER_ID and GUILD_ID are configured
        if self.config.owner_id and self.config.guild_id:
            try:
                await self.load_extension("src.commands.owner")
                logger.info(LogArea.NONE, "Loaded extension: src.commands.owner")
            except Exception as e:
                logger.error(LogArea.NONE, f"Failed to load owner commands: {e}")

    async def on_ready(self):
        logger.info(LogArea.NONE, f"Connected as: {self.user} (ID: {self.user.id})")
        logger.spacer()

        try:
            # Register global commands
            logger.info(LogArea.NONE, "Registering global commands...")
            registered = await self.tree.sync()
            logger.info(LogArea.NONE, f"Successfully registered {len(registered)} global commands")

            # List registered commands
            if registered:
                logger.info(LogArea.NONE, "Global commands registered:")
                for cmd in registered:
                    logger.info(LogArea.NONE, f"  - /{cmd.name}: {cmd.description}")
                    # Check if it's a group command with subcommands
                    if hasattr(cmd, "options"):
                        for option in cmd.options:
                            # Check if this option is a subgroup (has its own options)
                            if hasattr(option, "options") and option.options:
                                logger.info(LogArea.NONE, f"      - {option.name}: {option.description}")

            # Register guild-specific commands (admin and owner) if configured
            if self.config.guild_id:
                logger.spacer()
                logger.info(LogArea.NONE, f"Registering guild-specific commands to guild {self.config.guild_id}...")
                guild = discord.Object(id=self.config.guild_id)
                registered_guild = await self.tree.sync(guild=guild)
                logger.info(LogArea.NONE, f"Successfully registered {len(registered_guild)} commands to guild")

                # List guild-specific commands
                if registered_guild:
                    logger.info(LogArea.NONE, "Guild-specific commands registered:")
                    for cmd in registered_guild:
                        logger.info(LogArea.NONE, f"  - /{cmd.name}: {cmd.description}")
                        # Check if it's a group command with subcommands
                        if hasattr(cmd, "options"):
                            for option in cmd.options:
                                # Check if this option is a subgroup (has its own options)
                                if hasattr(option, "options") and option.options:
                                    logger.info(LogArea.NONE, f"      - {option.name}: {option.description}")
                                    for suboption in option.options:
                                        logger.info(LogArea.NONE, f"          - {suboption.name}: {suboption.description}")
                                else:
                                    logger.info(LogArea.NONE, f"      - {option.name}: {option.description}")

            logger.spacer()

        except Exception as e:
            logger.error(LogArea.NONE, f"Failed to register commands: {e}")
            logger.spacer()

        # Close the bot after registering
        await self.close()

    async def close(self):
        # Properly close the HTTP session
        if self.http is not None:
            await self.http.close()
        await super().close()


async def main(guild_id_override=None, owner_id_override=None):
    logger.spacer()
    logger.info(LogArea.NONE, "ClearTimer Bot - Command Registration")
    logger.spacer()
    logger.info(LogArea.NONE, "Starting command registration")

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Override guild_id if provided via command line
    if guild_id_override:
        config.guild_id = int(guild_id_override)
        logger.info(LogArea.NONE, f"Using guild ID from command line: {config.guild_id}")
    elif config.guild_id:
        logger.info(LogArea.NONE, f"Using guild ID from .env: {config.guild_id}")
    else:
        logger.info(LogArea.NONE, "No guild ID specified (owner commands will be global)")

    # Override owner_id if provided via command line
    if owner_id_override:
        config.owner_id = int(owner_id_override)
        logger.info(LogArea.NONE, f"Using owner ID from command line: {config.owner_id}")
    elif config.owner_id:
        logger.info(LogArea.NONE, f"Using owner ID from .env: {config.owner_id}")
    else:
        logger.info(LogArea.NONE, "No owner ID specified")

    # Create bot instance
    bot = CommandRegisterBot(config)

    # Run the bot
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info(LogArea.NONE, "Interrupted by user")
    except Exception as e:
        logger.error(LogArea.NONE, f"Error during registration: {e}")
    finally:
        # Ensure proper cleanup
        if bot and not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Register Discord bot slash commands")
    parser.add_argument(
        "--guild-id",
        type=str,
        help="Guild ID to register owner commands to (overrides .env setting)",
    )
    parser.add_argument(
        "--owner-id",
        type=str,
        help="Owner ID for owner-only commands (overrides .env setting)",
    )
    args = parser.parse_args()

    # Set up asyncio for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the registration
    asyncio.run(main(args.guild_id, args.owner_id))
