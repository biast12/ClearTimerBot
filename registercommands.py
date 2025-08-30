#!/usr/bin/env python3
"""
Command Sync Script - Registers slash commands with Discord
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


# Mock classes for command registration
class MockTimerParser:
    """Mock timer parser for command registration"""

    pass


class MockSchedulerService:
    """Mock scheduler service for command registration"""

    def __init__(self):
        self.timer_parser = MockTimerParser()


class MockDataService:
    """Mock data service for command registration"""

    def get_timezone(self, tz):
        return None


class MockMessageService:
    """Mock message service for command registration"""

    pass


class CommandSyncBot(commands.Bot):
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
        self.version = "2.0.0"

    async def setup_hook(self):
        # Load command cogs
        command_modules = [
            "src.commands.subscription",
            "src.commands.information",
            "src.commands.utility",
        ]

        for module in command_modules:
            try:
                await self.load_extension(module)
                print(f"[OK] Loaded extension: {module}")
            except Exception as e:
                print(f"[ERROR] Failed to load extension {module}: {e}")

        # Load owner commands if configured
        if self.config.is_owner_mode:
            try:
                await self.load_extension("src.commands.owner")
                print("[OK] Loaded owner commands")
            except Exception as e:
                print(f"[ERROR] Failed to load owner commands: {e}")

    async def on_ready(self):
        print(f"\n[BOT] Connected as: {self.user} (ID: {self.user.id})")
        print("=" * 50)

        try:
            # Sync global commands
            print("\n[SYNC] Syncing global commands...")
            synced = await self.tree.sync()
            print(f"[OK] Successfully synced {len(synced)} global commands")

            # List synced commands
            if synced:
                print("\nGlobal commands registered:")
                for cmd in synced:
                    print(f"  - /{cmd.name}: {cmd.description}")
                    # Check if it's a group command with subcommands
                    if hasattr(cmd, "options"):
                        for option in cmd.options:
                            print(
                                f"      - /{cmd.name} {option.name}: {option.description}"
                            )

            # Sync owner commands to specific guild if configured
            if self.config.is_owner_mode and self.config.guild_id:
                print(
                    f"\n[SYNC] Syncing owner commands to guild {self.config.guild_id}..."
                )
                guild = discord.Object(id=self.config.guild_id)
                synced_guild = await self.tree.sync(guild=guild)
                print(
                    f"[OK] Successfully synced {len(synced_guild)} commands to owner guild"
                )

                # List guild-specific commands
                if synced_guild:
                    print("\nOwner commands registered:")
                    for cmd in synced_guild:
                        print(f"  - /{cmd.name}: {cmd.description}")
                        # Check if it's a group command with subcommands
                        if hasattr(cmd, "options"):
                            for option in cmd.options:
                                print(
                                    f"      - /{cmd.name} {option.name}: {option.description}"
                                )

            print("\n[SUCCESS] Command synchronization complete!")
            print("=" * 50)

        except Exception as e:
            print(f"\n[ERROR] Failed to sync commands: {e}")
            print("=" * 50)

        # Close the bot after syncing
        await self.close()

    async def close(self):
        # Properly close the HTTP session
        if self.http is not None:
            await self.http.close()
        await super().close()


async def main(guild_id_override=None):
    print("=" * 50)
    print("ClearTimer Bot - Command Registration")
    print("=" * 50)

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Override guild_id if provided via command line
    if guild_id_override:
        config.guild_id = int(guild_id_override)
        print(f"[INFO] Using guild ID from command line: {config.guild_id}")
    elif config.guild_id:
        print(f"[INFO] Using guild ID from .env: {config.guild_id}")
    else:
        print("[INFO] No guild ID specified (owner commands will be global)")

    # Create bot instance
    bot = CommandSyncBot(config)

    # Run the bot
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
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
    args = parser.parse_args()

    # Set up asyncio for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the sync
    asyncio.run(main(args.guild_id))
