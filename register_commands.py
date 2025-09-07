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

sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import ConfigManager
from src.utils.logger import logger, LogArea


class MockScheduleParser:
    """Mock schedule parser for command registration"""

    pass


class MockSchedulerService:
    """Mock scheduler service for command registration"""

    def __init__(self):
        self.schedule_parser = MockScheduleParser()


class MockDataService:
    """Mock data service for command registration"""

    def get_timezones_list(self):
        return {}


class MockMessageService:
    """Mock message service for command registration"""

    pass


class CommandRegisterBot(commands.Bot):
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix=lambda bot, msg: None, intents=intents, help_command=None
        )

        self.config = config
        self.data_service = MockDataService()
        self.scheduler_service = MockSchedulerService()
        self.message_service = MockMessageService()

    async def setup_hook(self):
        from src.localization.discord_translator import ClearTimerTranslator

        translator = ClearTimerTranslator()
        await self.tree.set_translator(translator)

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

        if self.config.guild_id:
            try:
                await self.load_extension("src.commands.admin")
                logger.info(LogArea.NONE, "Loaded extension: src.commands.admin")
            except Exception as e:
                logger.error(LogArea.NONE, f"Failed to load admin commands: {e}")

        if self.config.owner_id and self.config.guild_id:
            try:
                await self.load_extension("src.commands.owner")
                logger.info(LogArea.NONE, "Loaded extension: src.commands.owner")
            except Exception as e:
                logger.error(LogArea.NONE, f"Failed to load owner commands: {e}")

    def display_commands(self, commands, command_type=""):
        """Display registered commands in a clean format"""
        if not commands:
            return

        slash_commands = []
        context_menus = []

        for cmd in commands:
            if hasattr(cmd, "type"):
                if cmd.type == discord.AppCommandType.user:
                    context_menus.append(cmd.name)
                elif cmd.type == discord.AppCommandType.message:
                    context_menus.append(cmd.name)
                else:
                    slash_commands.append(cmd)
            else:
                slash_commands.append(cmd)

        if slash_commands:
            logger.info(LogArea.NONE, f"{command_type} Slash commands registered:")
            for cmd in slash_commands:
                logger.info(LogArea.NONE, f"  - /{cmd.name}: {cmd.description}")
                if hasattr(cmd, "options"):
                    for option in cmd.options:
                        if hasattr(option, "required") or hasattr(option, "choices"):
                            continue

                        if hasattr(option, "options") and option.options:
                            logger.info(
                                LogArea.NONE,
                                f"      - {option.name}: {option.description}",
                            )
                            for suboption in option.options:
                                if hasattr(suboption, "required") or hasattr(
                                    suboption, "choices"
                                ):
                                    continue
                                logger.info(
                                    LogArea.NONE,
                                    f"          - {suboption.name}: {suboption.description}",
                                )
                        else:
                            logger.info(
                                LogArea.NONE,
                                f"      - {option.name}: {option.description}",
                            )

        if context_menus:
            logger.info(
                LogArea.NONE, f"{command_type} Context menu commands registered:"
            )
            for cmd_name in context_menus:
                logger.info(LogArea.NONE, f"  - {cmd_name}")

    async def on_ready(self):
        logger.info(LogArea.NONE, f"Connected as: {self.user} (ID: {self.user.id})")
        logger.spacer()

        try:
            logger.info(LogArea.NONE, "Registering global commands...")
            registered = await self.tree.sync()
            logger.info(
                LogArea.NONE,
                f"Successfully registered {len(registered)} global commands",
            )

            if registered:
                self.display_commands(registered, "Global")

            if self.config.guild_id:
                logger.spacer()
                logger.info(
                    LogArea.NONE,
                    f"Registering guild-specific commands to guild {self.config.guild_id}...",
                )
                guild = discord.Object(id=self.config.guild_id)
                registered_guild = await self.tree.sync(guild=guild)
                logger.info(
                    LogArea.NONE,
                    f"Successfully registered {len(registered_guild)} commands to guild",
                )

                if registered_guild:
                    self.display_commands(registered_guild, "Guild-specific")

            logger.spacer()

        except Exception as e:
            logger.error(LogArea.NONE, f"Failed to register commands: {e}")
            logger.spacer()

        await self.close()

    async def close(self):
        if self.http is not None:
            await self.http.close()
        await super().close()


async def main(guild_id_override=None, owner_id_override=None):
    logger.spacer()
    logger.info(LogArea.NONE, "ClearTimer Bot - Command Registration")
    logger.spacer()
    logger.info(LogArea.NONE, "Starting command registration")

    config_manager = ConfigManager()
    config = config_manager.load_config()

    if guild_id_override:
        config.guild_id = int(guild_id_override)
        logger.info(
            LogArea.NONE, f"Using guild ID from command line: {config.guild_id}"
        )
    elif config.guild_id:
        logger.info(LogArea.NONE, f"Using guild ID from .env: {config.guild_id}")
    else:
        logger.info(
            LogArea.NONE, "No guild ID specified (owner commands will be global)"
        )

    if owner_id_override:
        config.owner_id = int(owner_id_override)
        logger.info(
            LogArea.NONE, f"Using owner ID from command line: {config.owner_id}"
        )
    elif config.owner_id:
        logger.info(LogArea.NONE, f"Using owner ID from .env: {config.owner_id}")
    else:
        logger.info(LogArea.NONE, "No owner ID specified")

    bot = CommandRegisterBot(config)

    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info(LogArea.NONE, "Interrupted by user")
    except Exception as e:
        logger.error(LogArea.NONE, f"Error during registration: {e}")
    finally:
        if bot and not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
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

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main(args.guild_id, args.owner_id))
