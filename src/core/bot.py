import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

from src.models import BotConfig, GuildInfo
from src.services.server_data_service import DataService
from src.services.database_connection_manager import db_manager
from src.services.clear_job_scheduler_service import SchedulerService
from src.services.message_clearing_service import MessageService
from src.utils.logger import logger, LogArea


class ClearTimerBot(commands.Bot):
    def __init__(self, config: BotConfig, shard=None):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        shard_id = None
        shard_count = None
        if shard:
            shard_id, shard_count = shard

        allowed_mentions = discord.AllowedMentions(
            everyone=False,
            users=False,
            roles=False,
            replied_user=False
        )
        
        super().__init__(
            command_prefix=lambda bot, msg: None,
            intents=intents,
            help_command=None,
            allowed_mentions=allowed_mentions,
            shard_id=shard_id,
            shard_count=shard_count
        )

        self.config = config
        self.data_service = DataService()
        self.scheduler_service = SchedulerService(self.data_service)
        self.message_service = MessageService(self.data_service, self.scheduler_service)
        
        self.activity_dots = 0

        self.scheduler_service.register_channel_clear_callback(
            self.message_service.execute_channel_message_clear
        )
        self.scheduler_service.register_missed_clear_notification_callback(
            self.message_service.send_missed_clear_notification
        )


    @tasks.loop(seconds=2.0)
    async def rotate_activity(self):
        dots = "." * self.activity_dots
        
        total_subscriptions = 0
        all_servers = await self.data_service.get_all_servers()
        for server in all_servers.values():
            total_subscriptions += len(server.channels)
        
        activity = discord.CustomActivity(name=f"🧹 Cleaning up {total_subscriptions} channels{dots}")
        await self.change_presence(activity=activity)
        self.activity_dots = (self.activity_dots + 1) % 4

    async def setup_hook(self) -> None:
        await db_manager.connect()
        logger.info(LogArea.DATABASE, "Connected to MongoDB")

        await self.data_service.initialize()
        logger.info(LogArea.STARTUP, "Data service initialized")

        await self.load_commands()

    async def on_ready(self) -> None:
        if self.shard_id is not None:
            logger.info(LogArea.STARTUP, f"Shard {self.shard_id}/{self.shard_count - 1} ready: {self.user} (ID: {self.user.id})")
            logger.info(LogArea.STARTUP, f"Shard {self.shard_id} connected to {len(self.guilds)} guilds")
        else:
            logger.info(LogArea.STARTUP, f"Bot ready: {self.user} (ID: {self.user.id})")
            logger.info(LogArea.STARTUP, f"Connected to {len(self.guilds)} guilds")

        try:
            self.rotate_activity.start()

            await self._sync_server_cleanup_status()
            await self._update_server_names()
            await self._cleanup_deleted_channels()

            await self.scheduler_service.start()
            await self.scheduler_service.initialize_all_scheduled_jobs(self)
            logger.info(LogArea.SCHEDULER, "Scheduler jobs initialized")
            
            await self._update_all_view_messages()
            await self.data_service.cleanup_old_removed_servers()

            if self.shard_id is not None:
                logger.info(LogArea.STARTUP, f"Shard {self.shard_id} initialization complete!")
            else:
                logger.info(LogArea.STARTUP, "Bot initialization complete!")
        except Exception as e:
            error_id = await logger.log_error(
                LogArea.STARTUP,
                f"Critical error during bot initialization: {str(e)}",
                exception=e
            )
            logger.critical(LogArea.STARTUP, f"Bot initialization failed! Error ID: {error_id}")

    async def load_commands(self) -> None:
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

        if self.config.guild_id:
            try:
                await self.load_extension("src.commands.admin")
                logger.info(LogArea.STARTUP, "Loaded extension: src.commands.admin")
            except Exception as e:
                error_id = await logger.log_error(
                    LogArea.STARTUP,
                    "Failed to load admin commands",
                    exception=e
                )
                logger.error(LogArea.STARTUP, f"Failed to load admin commands. Error ID: {error_id}")
        
        if self.config.owner_id and self.config.guild_id:
            try:
                await self.load_extension("src.commands.owner")
                logger.info(LogArea.STARTUP, "Loaded extension: src.commands.owner")
            except Exception as e:
                error_id = await logger.log_error(
                    LogArea.STARTUP,
                    "Failed to load owner commands",
                    exception=e
                )
                logger.error(LogArea.STARTUP, f"Failed to load owner commands. Error ID: {error_id}")

    async def close(self) -> None:
        if getattr(self, 'restart_requested', False):
            logger.info(LogArea.STARTUP, "Restart requested, initiating graceful shutdown...")
        
        if self.rotate_activity.is_running():
            self.rotate_activity.cancel()
        
        await self.scheduler_service.shutdown()
        logger.info(LogArea.STARTUP, "Scheduler service shut down")
        
        await db_manager.disconnect()
        logger.info(LogArea.DATABASE, "Disconnected from MongoDB")
        
        await super().close()

    async def is_admin(self, user: discord.User) -> bool:
        """Check if user is an admin using database cache"""
        user_id = str(user.id)
        return await self.data_service.is_admin(user_id)
    
    def is_owner(self, user: discord.User) -> bool:
        """Legacy method for backward compatibility - now checks admin status"""
        if self.config.owner_id:
            return user.id == self.config.owner_id
        return False

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Handle when bot joins a server"""
        server_id = str(guild.id)
        
        guild_info = GuildInfo(
            guild_id=server_id,
            guild_name=guild.name,
            member_count=guild.member_count,
            owner_id=str(guild.owner_id),
            joined_at=datetime.now(timezone.utc),
            premium_tier=guild.premium_tier
        )

        removed_doc = await self.data_service.get_removed_server(server_id)

        if removed_doc:
            removed_servers_collection = db_manager.removed_servers
            await removed_servers_collection.delete_one({"_id": server_id})
            await self.data_service.invalidate_removed_server_cache(server_id)
            logger.info(
                LogArea.DISCORD,
                f"Bot rejoined server: {guild.name} (ID: {server_id})"
            )
            
            await self._cleanup_server_channels(guild)
        else:
            logger.info(LogArea.DISCORD, f"Bot joined new server: {guild.name} (ID: {server_id})")

        await self.data_service.add_server(guild)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Handle when bot leaves or is removed from a server"""
        server_id = str(guild.id)

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
                if not server.server_name or server.server_name != guild.name:
                    old_name = server.server_name or "(empty)"
                    await self.data_service.update_server_name(server_id, guild.name)
                    updated_count += 1
                    logger.debug(LogArea.DATABASE, f"Updated server name: {old_name} -> {guild.name} (ID: {server_id})")
            else:
                await self.data_service.add_server(guild)
                updated_count += 1
                logger.debug(LogArea.DATABASE, f"Added new server: {guild.name} (ID: {server_id})")
        
        if updated_count > 0:
            logger.info(LogArea.DATABASE, f"Updated {updated_count} server name(s)")

    async def _sync_server_cleanup_status(self) -> None:
        """Sync server cleanup status based on current guild membership on startup"""
        removed_servers_collection = db_manager.removed_servers
        
        all_servers = await self.data_service.get_all_servers()
        current_guild_ids = {str(guild.id) for guild in self.guilds}
        
        servers_to_mark_removed = []
        for server_id in all_servers.keys():
            if server_id not in current_guild_ids:
                server = all_servers[server_id]
                servers_to_mark_removed.append({
                    "_id": server_id,
                    "server_name": server.server_name,
                    "removed_at": datetime.now(timezone.utc),
                    "member_count": 0,
                })
        
        for removal_doc in servers_to_mark_removed:
            server_id = removal_doc["_id"]
            existing = await removed_servers_collection.find_one({"_id": server_id})
            if not existing:
                await removed_servers_collection.insert_one(removal_doc)
                await self.data_service.cache_removed_server(server_id, removal_doc)
                logger.info(LogArea.CLEANUP, f"Marked server {removal_doc['server_name']} (ID: {server_id}) as removed (bot not in server)")
        
        removed_servers = await removed_servers_collection.find().to_list(None)
        for removed_doc in removed_servers:
            server_id = removed_doc["_id"]
            if server_id in current_guild_ids:
                await removed_servers_collection.delete_one({"_id": server_id})
                await self.data_service.invalidate_removed_server_cache(server_id)
                guild = self.get_guild(int(server_id))
                guild_name = guild.name if guild else "Unknown"
                logger.info(LogArea.CLEANUP, f"Removed server {guild_name} (ID: {server_id}) from removal tracking (bot is in server)")
    
    async def _cleanup_deleted_channels(self) -> None:
        """Remove subscriptions for channels that no longer exist (only for servers bot is in)"""
        
        all_servers = await self.data_service.get_all_servers()
        
        for server_id, server in all_servers.items():
            removed_server = await self.data_service.get_removed_server(server_id)
            if removed_server:
                continue
            
            guild = self.get_guild(int(server_id))
            if not guild:
                continue
            
            subscribed_channels = list(server.channels.keys())
            
            for channel_id in subscribed_channels:
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    await self.data_service.remove_channel_subscription(server_id, channel_id)
    
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Handle when a channel is deleted"""
        if not isinstance(channel, discord.TextChannel):
            return
        
        server_id = str(channel.guild.id)
        channel_id = str(channel.id)
        
        server = await self.data_service.get_server(server_id)
        if server and channel_id in server.channels:
            if await self.data_service.remove_channel_subscription(server_id, channel_id):
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
                if await self.data_service.remove_channel_subscription(server_id, channel_id):
                    cleaned_count += 1
                    logger.info(
                        LogArea.CLEANUP,
                        f"Removed subscription for deleted channel {channel_id} in rejoined server {guild.name}"
                    )
                    
                    job_id = f"{server_id}_{channel_id}"
                    await self.scheduler_service.cancel_job_by_id(job_id)
        
        if cleaned_count > 0:
            logger.info(
                LogArea.CLEANUP,
                f"Cleaned up {cleaned_count} deleted channel(s) in rejoined server {guild.name}"
            )
    
    async def _update_all_view_messages(self) -> None:
        """Update all view messages to show current next run times on startup"""
        servers = await self.data_service.get_all_servers()
        updated_count = 0
        failed_count = 0
        
        for server_id, server in servers.items():
            # Skip servers bot is not in
            guild = self.get_guild(int(server_id))
            if not guild:
                continue
            
            for channel_id, channel_timer in server.channels.items():
                if not channel_timer.view_message_id:
                    continue
                
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    continue
                
                try:
                    next_run_time = self.scheduler_service.get_channel_next_clear_time(server_id, channel_id)
                    if next_run_time:
                        await self.message_service._update_view_message(
                            channel, 
                            channel_timer.view_message_id,
                            channel_timer.timer,
                            next_run_time
                        )
                        updated_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.debug(LogArea.STARTUP, f"Failed to update view message in {channel.name}: {e}")
        
        if updated_count > 0 or failed_count > 0:
            logger.info(
                LogArea.STARTUP, 
                f"View messages updated: {updated_count} successful, {failed_count} failed"
            )
