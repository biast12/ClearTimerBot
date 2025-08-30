import discord
from discord.ext import commands
from datetime import datetime, timezone

from src.core.config import BotConfig
from src.services.data_service import DataService
from src.services.database import db_manager
from src.services.scheduler_service import SchedulerService
from src.services.message_service import MessageService


class ClearTimerBot(commands.Bot):
    def __init__(self, config: BotConfig):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

        self.config = config
        self.data_service = DataService()
        self.scheduler_service = SchedulerService(self.data_service)
        self.message_service = MessageService(self.data_service, self.scheduler_service)

        # Set up service callbacks
        self.scheduler_service.set_clear_callback(
            self.message_service.clear_channel_messages
        )
        self.scheduler_service.set_notify_callback(
            self.message_service.notify_missed_clear
        )


    async def setup_hook(self) -> None:
        # Connect to MongoDB
        await db_manager.connect()

        # Initialize services
        await self.data_service.initialize()

        # Load command cogs
        await self.load_commands()

    async def on_ready(self) -> None:
        print(f"Bot ready: {self.user} (ID: {self.user.id})")
        print(f"Connected to {len(self.guilds)} guilds")

        # Set presence
        activity = discord.Game(name="Cleaning up the mess! 🧹")
        await self.change_presence(activity=activity)

        # Start scheduler and initialize jobs
        await self.scheduler_service.start()
        await self.scheduler_service.initialize_jobs(self)

        # Clean up old removed servers on startup
        await self.data_service.cleanup_old_removed_servers()

        print("Bot initialization complete!")

    async def load_commands(self) -> None:
        # Load standard commands
        command_modules = [
            "src.commands.subscription",
            "src.commands.information",
            "src.commands.utility",
        ]

        for module in command_modules:
            try:
                await self.load_extension(module)
                print(f"Loaded extension: {module}")
            except Exception as e:
                print(f"Failed to load extension {module}: {e}")

        # Load owner commands if configured
        if self.config.is_owner_mode:
            try:
                await self.load_extension("src.commands.owner")
                print("Loaded owner commands")
            except Exception as e:
                print(f"Failed to load owner commands: {e}")

    async def close(self) -> None:
        await self.scheduler_service.shutdown()
        await db_manager.disconnect()
        await super().close()

    def is_owner(self, user: discord.User) -> bool:
        if self.config.owner_id:
            return user.id == self.config.owner_id
        return False

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Handle when bot joins a server"""
        server_id = str(guild.id)

        # Check if this server was previously removed
        removed_servers_collection = db_manager.removed_servers
        removed_doc = await removed_servers_collection.find_one({"_id": server_id})

        if removed_doc:
            # Server is rejoining, remove it from removed_servers collection
            await removed_servers_collection.delete_one({"_id": server_id})
            print(
                f"Bot rejoined server: {guild.name} (ID: {server_id}) - Removed from removal tracking"
            )
        else:
            print(f"Bot joined new server: {guild.name} (ID: {server_id})")

        # Add or update server in data service
        await self.data_service.add_server(server_id, guild.name)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Handle when bot leaves or is removed from a server"""
        server_id = str(guild.id)

        # Add to removed_servers collection with timestamp
        removed_servers_collection = db_manager.removed_servers
        await removed_servers_collection.replace_one(
            {"_id": server_id},
            {
                "_id": server_id,
                "server_name": guild.name,
                "removed_at": datetime.now(timezone.utc),
                "member_count": guild.member_count if guild else 0,
            },
            upsert=True,
        )

        print(
            f"Bot removed from server: {guild.name} (ID: {server_id}) - Added to removal tracking"
        )
