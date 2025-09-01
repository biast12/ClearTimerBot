import discord
from discord.ext import commands
from datetime import datetime, timezone

from src.models import BotConfig, GuildInfo, CommandUsage
from src.services.server_data_service import DataService
from src.services.database_connection_manager import db_manager
from src.services.clear_job_scheduler_service import SchedulerService
from src.services.message_clearing_service import MessageService
from src.utils.logger import logger, LogArea


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
        self.scheduler_service.register_channel_clear_callback(
            self.message_service.execute_channel_message_clear
        )
        self.scheduler_service.register_missed_clear_notification_callback(
            self.message_service.send_missed_clear_notification
        )


    async def setup_hook(self) -> None:
        # Connect to database first
        await db_manager.connect()
        logger.info(LogArea.DATABASE, "Connected to MongoDB")

        # Initialize data service
        await self.data_service.initialize()
        logger.info(LogArea.STARTUP, "Data service initialized")

        # Load command cogs last
        await self.load_commands()

    async def on_ready(self) -> None:
        logger.info(LogArea.STARTUP, f"Bot ready: {self.user} (ID: {self.user.id})")
        logger.info(LogArea.STARTUP, f"Connected to {len(self.guilds)} guilds")

        try:
            # Set bot presence first
            activity = discord.CustomActivity(name="Cleaning up the mess! 🧹")
            await self.change_presence(activity=activity)

            # Sync server data with current guild membership
            await self._sync_server_cleanup_status()
            
            # Update server names for all connected guilds
            await self._update_server_names()
            
            # Clean up subscriptions for deleted channels
            await self._cleanup_deleted_channels()

            # Start the scheduler service
            await self.scheduler_service.start()
            
            # Initialize scheduled jobs for all subscriptions
            # Requires scheduler to be running
            await self.scheduler_service.initialize_all_scheduled_jobs(self)
            logger.info(LogArea.SCHEDULER, "Scheduler jobs initialized")

            # Perform maintenance tasks (cleanup old removed servers)
            await self.data_service.cleanup_old_removed_servers()

            logger.info(LogArea.STARTUP, "Bot initialization complete!")
        except Exception as e:
            error_id = await logger.log_error(
                LogArea.STARTUP,
                f"Critical error during bot initialization: {str(e)}",
                exception=e
            )
            logger.critical(LogArea.STARTUP, f"Bot initialization failed! Error ID: {error_id}")

    async def load_commands(self) -> None:
        # Load standard commands
        command_modules = [
            "src.commands.subscription",
            "src.commands.general",
        ]

        for module in command_modules:
            try:
                await self.load_extension(module)
                logger.info(LogArea.STARTUP, f"Loaded extension: {module}")
            except Exception as e:
                error_id = await logger.log_error(
                    LogArea.STARTUP,
                    f"Failed to load extension {module}",
                    exception=e
                )
                logger.error(LogArea.STARTUP, f"Failed to load extension {module}. Error ID: {error_id}")

        # Load admin commands if GUILD_ID is configured
        if self.config.guild_id:
            try:
                await self.load_extension("src.commands.admin")
                logger.info(LogArea.STARTUP, "Loading admin commands")
            except Exception as e:
                error_id = await logger.log_error(
                    LogArea.STARTUP,
                    "Failed to load admin commands",
                    exception=e
                )
                logger.error(LogArea.STARTUP, f"Failed to load admin commands. Error ID: {error_id}")
        
        # Load owner commands if both OWNER_ID and GUILD_ID are configured
        if self.config.owner_id and self.config.guild_id:
            try:
                await self.load_extension("src.commands.owner")
                logger.info(LogArea.STARTUP, "Loading owner commands")
            except Exception as e:
                error_id = await logger.log_error(
                    LogArea.STARTUP,
                    "Failed to load owner commands",
                    exception=e
                )
                logger.error(LogArea.STARTUP, f"Failed to load owner commands. Error ID: {error_id}")

    async def close(self) -> None:
        # Stop scheduler first (prevents new jobs from running)
        await self.scheduler_service.shutdown()
        logger.info(LogArea.STARTUP, "Scheduler service shut down")
        
        # Disconnect from database
        await db_manager.disconnect()
        logger.info(LogArea.DATABASE, "Disconnected from MongoDB")
        
        # Close Discord connection last
        await super().close()

    async def is_admin(self, user: discord.User) -> bool:
        """Check if user is an admin using database cache"""
        user_id = str(user.id)
        return await self.data_service.is_admin(user_id)
    
    def is_owner(self, user: discord.User) -> bool:
        """Legacy method for backward compatibility - now checks admin status"""
        # This is a synchronous wrapper that needs to be replaced with async calls
        # For now, we'll check the legacy owner_id for compatibility
        if self.config.owner_id:
            return user.id == self.config.owner_id
        return False

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Handle when bot joins a server"""
        server_id = str(guild.id)
        
        # Create GuildInfo model for tracking
        guild_info = GuildInfo(
            guild_id=server_id,
            guild_name=guild.name,
            member_count=guild.member_count,
            owner_id=str(guild.owner_id),
            joined_at=datetime.now(timezone.utc),
            premium_tier=guild.premium_tier
        )

        # Check if this server was previously removed (using cache)
        removed_doc = await self.data_service.get_removed_server(server_id)

        if removed_doc:
            # Server is rejoining, remove it from removed_servers collection
            removed_servers_collection = db_manager.removed_servers
            await removed_servers_collection.delete_one({"_id": server_id})
            await self.data_service.invalidate_removed_server_cache(server_id)
            logger.info(
                LogArea.DISCORD,
                f"Bot rejoined server: {guild.name} (ID: {server_id})"
            )
            
            # Clean up any deleted channels for this rejoined server
            await self._cleanup_server_channels(guild)
        else:
            logger.info(LogArea.DISCORD, f"Bot joined new server: {guild.name} (ID: {server_id})")

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

        logger.info(
            LogArea.DISCORD,
            f"Bot removed from server: {guild.name} (ID: {server_id})"
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
                    logger.debug(LogArea.DATABASE, f"Updated server name: {old_name} -> {guild.name} (ID: {server_id})")
            else:
                # Server not in database, add it
                await self.data_service.add_server(server_id, guild.name)
                updated_count += 1
                logger.debug(LogArea.DATABASE, f"Added new server: {guild.name} (ID: {server_id})")
        
        if updated_count > 0:
            logger.info(LogArea.DATABASE, f"Updated {updated_count} server name(s)")

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
                logger.info(LogArea.CLEANUP, f"Marked server {removal_doc['server_name']} (ID: {server_id}) as removed (bot not in server)")
        
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
                logger.info(LogArea.CLEANUP, f"Removed server {guild_name} (ID: {server_id}) from removal tracking (bot is in server)")
    
    async def _cleanup_deleted_channels(self) -> None:
        """Remove subscriptions for channels that no longer exist (only for servers bot is in)"""
        
        all_servers = await self.data_service.get_all_servers()
        
        for server_id, server in all_servers.items():
            # Check if server is in removed_servers (bot was removed)
            removed_server = await self.data_service.get_removed_server(server_id)
            if removed_server:
                # Bot is not in this server, skip cleanup to preserve subscriptions
                continue
            
            guild = self.get_guild(int(server_id))
            if not guild:
                # Server not in removed_servers but bot doesn't have access
                # This shouldn't happen, but skip to be safe
                continue
            
            # Get list of channel IDs that are subscribed
            subscribed_channels = list(server.channels.keys())
            
            for channel_id in subscribed_channels:
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    # Channel doesn't exist, remove subscription
                    await self.data_service.remove_channel_subscription(server_id, channel_id)
    
    async def on_command(self, ctx: commands.Context) -> None:
        """Track command usage"""
        command_usage = CommandUsage(
            command_name=ctx.command.name if ctx.command else "unknown",
            user_id=str(ctx.author.id),
            guild_id=str(ctx.guild.id) if ctx.guild else None,
            timestamp=datetime.now(timezone.utc),
            success=True
        )
        logger.debug(LogArea.COMMANDS, f"Command executed: {command_usage.command_name} by user {ctx.author}")
    
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Track command errors"""
        command_usage = CommandUsage(
            command_name=ctx.command.name if ctx.command else "unknown",
            user_id=str(ctx.author.id),
            guild_id=str(ctx.guild.id) if ctx.guild else None,
            timestamp=datetime.now(timezone.utc),
            success=False,
            error_message=str(error)
        )
        
        # Log the error
        await logger.log_error(
            LogArea.COMMANDS,
            f"Command error: {command_usage.command_name}",
            exception=error,
            user_id=command_usage.user_id,
            guild_id=command_usage.guild_id,
            command=command_usage.command_name
        )
    
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Handle when a channel is deleted"""
        if not isinstance(channel, discord.TextChannel):
            return
        
        server_id = str(channel.guild.id)
        channel_id = str(channel.id)
        
        # Check if this channel had a subscription
        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            # Remove the subscription
            if await self.data_service.remove_channel_subscription(server_id, channel_id):

                # Cancel the scheduled job if it exists
                job_id = f"{server_id}_{channel_id}"
                if await self.scheduler_service.cancel_job_by_id(job_id):
                    logger.debug(LogArea.SCHEDULER, f"Cancelled scheduled job for deleted channel: {job_id}")
    
    async def _cleanup_server_channels(self, guild: discord.Guild) -> None:
        """Clean up deleted channels when bot rejoins a server"""
        server_id = str(guild.id)
        server = await self.data_service.get_server(server_id)
        
        if not server or not server.channels:
            return
        
        cleaned_count = 0
        subscribed_channels = list(server.channels.keys())
        
        for channel_id in subscribed_channels:
            channel = guild.get_channel(int(channel_id))
            if not channel:
                # Channel was deleted while bot was away
                if await self.data_service.remove_channel_subscription(server_id, channel_id):
                    cleaned_count += 1
                    logger.info(
                        LogArea.CLEANUP,
                        f"Removed subscription for deleted channel {channel_id} in rejoined server {guild.name}"
                    )
                    
                    # Cancel any scheduled job
                    job_id = f"{server_id}_{channel_id}"
                    await self.scheduler_service.cancel_job_by_id(job_id)
        
        if cleaned_count > 0:
            logger.info(
                LogArea.CLEANUP,
                f"Cleaned up {cleaned_count} deleted channel(s) in rejoined server {guild.name}"
            )
