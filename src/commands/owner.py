import discord
from discord import app_commands
from discord.ext import commands
from src.utils.logger import logger, LogArea


class OwnerCommands(
    commands.GroupCog, group_name="owner", description="Owner-only management commands"
):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.scheduler_service = bot.scheduler_service

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.bot.is_owner(interaction.user):
            from src.components.owner import OwnerOnlyView
            view = OwnerOnlyView()
            await interaction.response.send_message(view=view, ephemeral=True)
            return False
        return True
    
    # Create subgroups for blacklist, error, and force commands
    blacklist_group = app_commands.Group(
        name="blacklist",
        description="Manage server blacklist",
        parent=None
    )
    
    error_group = app_commands.Group(
        name="error",
        description="Manage error logs",
        parent=None
    )
    
    force_group = app_commands.Group(
        name="force",
        description="Force management actions",
        parent=None
    )
    
    @app_commands.command(
        name="stats", description="View bot statistics"
    )
    @app_commands.describe(
        server_id="Server ID to get specific stats for (optional)"
    )
    async def stats(self, interaction: discord.Interaction, server_id: str = None):
        await interaction.response.defer(thinking=True)
        
        # If server_id is provided, show server-specific stats
        if server_id:
            server = await self.data_service.get_server(server_id)
            
            # Check if server exists in database
            if not server:
                from src.components.owner import ServerNotFoundView
                view = ServerNotFoundView(server_id)
                await interaction.followup.send(view=view)
                return
            
            # Get guild info
            guild = self.bot.get_guild(int(server_id))
            server_name = guild.name if guild else (server.server_name or "Unknown")
            
            # Check blacklist status
            blacklist = await self.data_service.get_blacklist()
            is_blacklisted = server_id in blacklist
            
            # Count server-specific errors
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.db.errors
            server_errors = await errors_collection.count_documents({"server_id": server_id})
            
            # Get channel details
            channel_count = len(server.channels)
            
            from src.components.owner import ServerStatsView
            view = ServerStatsView(
                server_id=server_id,
                server_name=server_name,
                channel_count=channel_count,
                is_blacklisted=is_blacklisted,
                error_count=server_errors,
                bot=self.bot,
                channels=server.channels
            )
            await interaction.followup.send(view=view)
        else:
            # Show overall bot statistics
            servers = await self.data_service.get_all_servers()
            blacklist = await self.data_service.get_blacklist()
            
            # Count servers and channels
            total_servers = len(self.bot.guilds)
            total_channels = sum(len(server.channels) for server in servers.values())
            removed_servers = len([s for s in servers.values() if not s.channels])
            blacklisted_servers = len(blacklist)
            
            # Count errors
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.db.errors
            error_count = await errors_collection.count_documents({})
            
            # Simple stats display
            from src.components.owner import SimpleStatsView
            
            view = SimpleStatsView(
                total_servers=total_servers,
                total_channels=total_channels,
                removed_servers=removed_servers,
                blacklisted_servers=blacklisted_servers,
                error_count=error_count
            )
            await interaction.followup.send(view=view)


    @blacklist_group.command(
        name="add", description="Add a server to the blacklist"
    )
    @app_commands.describe(
        server_id="Server ID to blacklist",
        reason="Reason for blacklisting (optional)"
    )
    async def blacklist_add(self, interaction: discord.Interaction, server_id: str, reason: str = "No reason provided"):
        # Try to get the server name if the bot is in the server
        guild = self.bot.get_guild(int(server_id))
        server_name = guild.name if guild else "Unknown"
        
        if await self.data_service.add_to_blacklist(server_id, server_name, reason=reason):
            await self.data_service.save_blacklist()

            # Remove any existing subscriptions but keep server in database
            server = await self.data_service.get_server(server_id)
            if server:
                for channel_id in list(server.channels.keys()):
                    self.scheduler_service.remove_channel_clear_job(server_id, channel_id)
                    server.remove_channel(channel_id)
                # Keep server in database even with no channels
                await self.data_service.save_servers()

            from src.components.owner import BlacklistAddSuccessView
            view = BlacklistAddSuccessView(server_name, server_id, reason)
            await interaction.response.send_message(view=view)
        else:
            from src.components.owner import BlacklistAddAlreadyView
            view = BlacklistAddAlreadyView(server_id)
            await interaction.response.send_message(view=view)

    @blacklist_group.command(
        name="remove", description="Remove a server from the blacklist"
    )
    @app_commands.describe(server_id="Server ID to remove from blacklist")
    async def blacklist_remove(self, interaction: discord.Interaction, server_id: str):
        if await self.data_service.remove_from_blacklist(server_id):
            await self.data_service.save_blacklist()
            from src.components.owner import BlacklistRemoveSuccessView
            view = BlacklistRemoveSuccessView(server_id)
            await interaction.response.send_message(view=view)
        else:
            from src.components.owner import BlacklistRemoveNotFoundView
            view = BlacklistRemoveNotFoundView(server_id)
            await interaction.response.send_message(view=view)

    @blacklist_group.command(
        name="check", description="Check if a server is blacklisted"
    )
    @app_commands.describe(server_id="Server ID to check blacklist status")
    async def blacklist_check(self, interaction: discord.Interaction, server_id: str):
        # Check if server is blacklisted
        blacklist_entries = await self.data_service.get_blacklist_entries()
        
        if server_id not in blacklist_entries:
            from src.components.owner import BlacklistCheckNotFoundView
            view = BlacklistCheckNotFoundView(server_id)
            await interaction.response.send_message(view=view)
            return
        
        # Get the blacklist entry
        entry = blacklist_entries[server_id]
        
        # Try to get current server name from bot's cache
        guild = self.bot.get_guild(int(server_id))
        server_name = guild.name if guild else (entry.server_name or "Unknown")
        
        from src.components.owner import BlacklistCheckFoundView
        view = BlacklistCheckFoundView(server_id, server_name, entry)
        await interaction.response.send_message(view=view)

    @app_commands.command(name="reload_cache", description="Reload all caches from database")
    async def reload_cache(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        try:
            # Clear all multi-level caches
            await self.data_service._cache.clear_all()
            
            # Clear internal caches
            self.data_service._servers_cache.clear()
            self.data_service._blacklist_cache.clear()
            self.data_service._blacklist_names_cache.clear()
            self.data_service._blacklist_entries_cache.clear()
            self.data_service._timezones_cache.clear()
            
            # Mark as uninitialized to force reload
            self.data_service._initialized = False
            
            # Reinitialize to reload from database
            await self.data_service.initialize()
            
            # Get stats after reload
            servers_count = len(self.data_service._servers_cache)
            blacklist_count = len(self.data_service._blacklist_cache)
            timezones_count = len(self.data_service._timezones_cache)
            
            # Cache reload display
            from src.components.owner import CacheReloadView
            
            view = CacheReloadView(servers_count, blacklist_count, timezones_count)
            await interaction.followup.send(view=view)
            
        except Exception as e:
            from src.components.owner import CacheReloadErrorView
            view = CacheReloadErrorView(str(e))
            await interaction.followup.send(view=view)

    @error_group.command(
        name="check", description="Check an error by its ID"
    )
    @app_commands.describe(error_id="The error ID to check")
    async def error_check(self, interaction: discord.Interaction, error_id: str):
        await interaction.response.defer(thinking=True)
        
        # Get error from database
        error_doc = await logger.get_error(error_id)
        
        if not error_doc:
            from src.components.owner import ErrorNotFoundView
            view = ErrorNotFoundView(error_id)
            await interaction.followup.send(view=view)
            return
        
        # Error details display
        from src.components.owner import ErrorDetailsView
        
        view = ErrorDetailsView(error_doc, self.bot)
        await interaction.followup.send(view=view)

    @error_group.command(
        name="delete", description="Delete an error by its ID"
    )
    @app_commands.describe(error_id="The error ID to delete")
    async def error_delete(self, interaction: discord.Interaction, error_id: str):
        await interaction.response.defer(thinking=True)
        
        # Delete error from database
        success = await logger.delete_error(error_id)
        
        if success:
            from src.components.owner import ErrorDeleteSuccessView
            view = ErrorDeleteSuccessView(error_id)
            await interaction.followup.send(view=view)
        else:
            from src.components.owner import ErrorDeleteFailedView
            view = ErrorDeleteFailedView(error_id)
            await interaction.followup.send(view=view)

    @error_group.command(
        name="list", description="List recent errors"
    )
    @app_commands.describe(limit="Number of errors to show (default: 10, max: 25)")
    async def error_list(self, interaction: discord.Interaction, limit: int = 10):
        await interaction.response.defer(thinking=True)
        
        # Validate limit
        limit = min(max(1, limit), 25)
        
        # Get recent errors
        errors = await logger.get_recent_errors(limit)
        
        if not errors:
            from src.components.owner import NoErrorsView
            view = NoErrorsView()
            await interaction.followup.send(view=view)
            return
        
        # Error list display
        from src.components.owner import ErrorListView
        
        view = ErrorListView(errors)
        await interaction.followup.send(view=view)

    @error_group.command(
        name="clear", description="Clear all errors from the database"
    )
    async def error_clear(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        from src.services.database_connection_manager import db_manager
        
        try:
            errors_collection = db_manager.db.errors
            result = await errors_collection.delete_many({})
            from src.components.owner import ErrorsClearedView
            view = ErrorsClearedView(result.deleted_count)
            await interaction.followup.send(view=view)
        except Exception as e:
            error_id = await logger.log_error(
                LogArea.DATABASE,
                "Failed to clear errors from database",
                exception=e
            )
            from src.components.owner import ErrorsClearFailedView
            view = ErrorsClearFailedView(error_id)
            await interaction.followup.send(view=view)


    @force_group.command(
        name="remove_server", description="Force remove all subscriptions for a server"
    )
    @app_commands.describe(id="Server ID to remove all subscriptions from")
    async def force_remove_server(self, interaction: discord.Interaction, id: str):
        await interaction.response.defer(thinking=True)

        # Get all servers
        servers = await self.data_service.get_all_servers()

        # Check if server exists
        if id not in servers:
            from src.components.owner import ForceUnsubNotFoundView
            view = ForceUnsubNotFoundView(id)
            await interaction.followup.send(view=view)
            return

        server = servers[id]
        channels_removed = len(server.channels)

        # Remove all jobs and channels for this server
        for channel_id in list(server.channels.keys()):
            self.scheduler_service.remove_channel_clear_job(id, channel_id)
            server.remove_channel(channel_id)

        # Keep server in database even with no channels
        await self.data_service.save_servers()

        from src.components.owner import ForceUnsubSuccessView
        view = ForceUnsubSuccessView("server", id, channels_removed)
        await interaction.followup.send(view=view)

    @force_group.command(
        name="remove_channel", description="Force remove a specific channel subscription"
    )
    @app_commands.describe(id="Channel ID to unsubscribe")
    async def force_remove_channel(self, interaction: discord.Interaction, id: str):
        await interaction.response.defer(thinking=True)

        # Get all servers to find which one has this channel
        servers = await self.data_service.get_all_servers()

        # Find which server has this channel
        for server_id, server in servers.items():
            if id in server.channels:
                # Remove job
                self.scheduler_service.remove_channel_clear_job(server_id, id)

                # Remove from data service
                server.remove_channel(id)
                await self.data_service.save_servers()

                from src.components.owner import ForceUnsubSuccessView
                view = ForceUnsubSuccessView("channel", id, server_id=server_id)
                await interaction.followup.send(view=view)
                return

        # Channel not found in any server
        from src.components.owner import ForceUnsubNotFoundView
        view = ForceUnsubNotFoundView(id)
        await interaction.followup.send(view=view)


async def setup(bot):
    if bot.config.is_owner_mode and bot.config.guild_id:
        await bot.add_cog(
            OwnerCommands(bot), guild=discord.Object(id=bot.config.guild_id)
        )
