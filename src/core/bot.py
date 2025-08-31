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

        # Update server names for all connected guilds
        await self._update_server_names()

        # Sync server cleanup status based on current guild membership
        await self._sync_server_cleanup_status()

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

        # Check if this server was previously removed (using cache)
        removed_doc = await self.data_service.get_removed_server(server_id)

        if removed_doc:
            # Server is rejoining, remove it from removed_servers collection
            removed_servers_collection = db_manager.removed_servers
            await removed_servers_collection.delete_one({"_id": server_id})
            await self.data_service.invalidate_removed_server_cache(server_id)
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
        removal_doc = {
            "_id": server_id,
            "server_name": guild.name,
            "removed_at": datetime.now(timezone.utc),
            "member_count": guild.member_count if guild else 0,
        }
        await removed_servers_collection.replace_one(
            {"_id": server_id},
            removal_doc,
            upsert=True,
        )
        
        # Cache the removal document
        await self.data_service.cache_removed_server(server_id, removal_doc)

        print(
            f"Bot removed from server: {guild.name} (ID: {server_id}) - Added to removal tracking"
        )

    async def _update_server_names(self) -> None:
        """Update server names for all connected guilds on startup"""
        updated_count = 0
        
        for guild in self.guilds:
            server_id = str(guild.id)
            server = await self.data_service.get_server(server_id)
            
            if server:
                # Check if server name is empty or different
                if not server.server_name or server.server_name != guild.name:
                    old_name = server.server_name or "(empty)"
                    await self.data_service.update_server_name(server_id, guild.name)
                    updated_count += 1
                    print(f"Updated server name: {old_name} -> {guild.name} (ID: {server_id})")
            else:
                # Server not in database, add it
                await self.data_service.add_server(server_id, guild.name)
                updated_count += 1
                print(f"Added new server: {guild.name} (ID: {server_id})")
        
        if updated_count > 0:
            print(f"Updated {updated_count} server name(s)")

    async def _sync_server_cleanup_status(self) -> None:
        """Sync server cleanup status based on current guild membership on startup"""
        removed_servers_collection = db_manager.removed_servers
        
        # Get all servers from database
        all_servers = await self.data_service.get_all_servers()
        
        # Get current guild IDs
        current_guild_ids = {str(guild.id) for guild in self.guilds}
        
        # Check each server in database
        servers_to_mark_removed = []
        for server_id in all_servers.keys():
            if server_id not in current_guild_ids:
                # Bot is not in this server, should be marked as removed
                server = all_servers[server_id]
                servers_to_mark_removed.append({
                    "_id": server_id,
                    "server_name": server.server_name,
                    "removed_at": datetime.now(timezone.utc),
                    "member_count": 0,  # Unknown since bot is not in the server
                })
        
        # Add servers to removed_servers collection if not already there
        for removal_doc in servers_to_mark_removed:
            server_id = removal_doc["_id"]
            # Check if already in removed_servers
            existing = await removed_servers_collection.find_one({"_id": server_id})
            if not existing:
                await removed_servers_collection.insert_one(removal_doc)
                await self.data_service.cache_removed_server(server_id, removal_doc)
                print(f"Marked server {removal_doc['server_name']} (ID: {server_id}) as removed (bot not in server)")
        
        # Check removed_servers collection for servers bot is currently in
        removed_servers = await removed_servers_collection.find().to_list(None)
        for removed_doc in removed_servers:
            server_id = removed_doc["_id"]
            if server_id in current_guild_ids:
                # Bot is in this server, remove from removed_servers
                await removed_servers_collection.delete_one({"_id": server_id})
                await self.data_service.invalidate_removed_server_cache(server_id)
                guild = self.get_guild(int(server_id))
                guild_name = guild.name if guild else "Unknown"
                print(f"Removed server {guild_name} (ID: {server_id}) from removal tracking (bot is in server)")
