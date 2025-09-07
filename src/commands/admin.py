import discord
from discord import app_commands
from discord.ext import commands
from src.utils.logger import logger, LogArea
from src.localization import get_translator, get_command_description


class AdminCommands(
    commands.GroupCog, 
    group_name="admin", 
    description=get_command_description("admin"),
    group_auto_locale_strings=False
):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.scheduler_service = bot.scheduler_service

    async def _check_admin_permission_before_defer(self, interaction: discord.Interaction) -> bool:
        """Check if user has admin permissions"""
        is_owner = self.bot.is_owner(interaction.user)
        is_admin = await self.bot.is_admin(interaction.user)
        
        if not (is_owner or is_admin):
            # Get translator for localization
            translator = None
            if interaction.guild:
                try:
                    translator = await get_translator(str(interaction.guild.id), self.data_service)
                except:
                    pass
            
            from src.components.admin import AdminOnlyView
            view = AdminOnlyView(translator=translator)
            await interaction.followup.send(view=view, ephemeral=True)
            return False
        return True
    
    blacklist_group = app_commands.Group(
        name="blacklist",
        description=get_command_description("admin.blacklist"),
        parent=None,
        auto_locale_strings=False
    )
    
    error_group = app_commands.Group(
        name="error",
        description=get_command_description("admin.error"),
        parent=None,
        auto_locale_strings=False
    )
    
    force_group = app_commands.Group(
        name="force",
        description=get_command_description("admin.force"),
        parent=None,
        auto_locale_strings=False
    )
    
    @app_commands.command(
        name="stats", 
        description=get_command_description("admin.stats"),
        auto_locale_strings=False
    )
    @app_commands.describe(
        server_id="Server ID to get specific stats for (optional)"
    )
    async def stats(self, interaction: discord.Interaction, server_id: str = None):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        # Get translator for localization
        translator = None
        if interaction.guild:
            try:
                translator = await get_translator(str(interaction.guild.id), self.data_service)
            except:
                pass
        
        if server_id:
            server = await self.data_service.get_server(server_id)
            
            if not server:
                from src.components.admin import ServerNotFoundView
                view = ServerNotFoundView(server_id, translator=translator)
                await interaction.followup.send(view=view)
                return
            
            guild = self.bot.get_guild(int(server_id))
            server_name = guild.name if guild else (server.server_name or "Unknown")
            
            blacklist = await self.data_service.get_blacklist()
            is_blacklisted = server_id in blacklist
            
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.db.errors
            
            cache_key = f"stats:errors:server:{server_id}"
            server_errors = await self.data_service._cache.get(cache_key)
            
            if server_errors is None:
                server_errors = await errors_collection.count_documents({"server_id": server_id})
                await self.data_service._cache.set(cache_key, server_errors, cache_level="memory", ttl=300)
            
            channel_count = len(server.channels)
            
            from src.components.admin import ServerStatsView
            view = ServerStatsView(
                server_id=server_id,
                server_name=server_name,
                channel_count=channel_count,
                is_blacklisted=is_blacklisted,
                error_count=server_errors,
                bot=self.bot,
                channels=server.channels,
                translator=translator
            )
            await interaction.followup.send(view=view)
        else:
            servers = await self.data_service.get_all_servers()
            blacklist = await self.data_service.get_blacklist()
            
            total_servers = len(self.bot.guilds)
            total_channels = sum(len(server.channels) for server in servers.values())
            removed_servers = len([s for s in servers.values() if not s.channels])
            blacklisted_servers = len(blacklist)
            
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.db.errors
            
            cache_key = "stats:errors:total"
            error_count = await self.data_service._cache.get(cache_key)
            
            if error_count is None:
                error_count = await errors_collection.count_documents({})
                await self.data_service._cache.set(cache_key, error_count, cache_level="memory", ttl=300)
            
            from src.components.admin import SimpleStatsView
            
            view = SimpleStatsView(
                total_servers=total_servers,
                total_channels=total_channels,
                removed_servers=removed_servers,
                blacklisted_servers=blacklisted_servers,
                error_count=error_count,
                translator=translator
            )
            await interaction.followup.send(view=view)


    @blacklist_group.command(
        name="add", 
        description=get_command_description("admin.blacklist.add"),
        auto_locale_strings=False
    )
    @app_commands.describe(
        server_id="Server ID to blacklist",
        reason="Reason for blacklisting (optional)"
    )
    async def blacklist_add(self, interaction: discord.Interaction, server_id: str, reason: str = "No reason provided"):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        # Get translator for localization
        translator = None
        if interaction.guild:
            try:
                translator = await get_translator(str(interaction.guild.id), self.data_service)
            except:
                pass
        
        guild = self.bot.get_guild(int(server_id))
        server_name = guild.name if guild else "Unknown"
        blacklisted_by = str(interaction.user.id)
        
        if await self.data_service.add_to_blacklist(server_id, server_name, reason=reason, blacklisted_by=blacklisted_by):
            await self.data_service.save_blacklist()

            server = await self.data_service.get_server(server_id)
            if server:
                for channel_id in list(server.channels.keys()):
                    self.scheduler_service.remove_channel_clear_job(server_id, channel_id)
                    server.remove_channel(channel_id)
                await self.data_service.save_servers()

            from src.components.admin import BlacklistAddSuccessView
            view = BlacklistAddSuccessView(server_name, server_id, reason, translator=translator)
            await interaction.followup.send(view=view)
        else:
            from src.components.admin import BlacklistAddAlreadyView
            view = BlacklistAddAlreadyView(server_id, translator=translator)
            await interaction.followup.send(view=view)

    @blacklist_group.command(
        name="remove", 
        description=get_command_description("admin.blacklist.remove"),
        auto_locale_strings=False
    )
    @app_commands.describe(server_id="Server ID to remove from blacklist")
    async def blacklist_remove(self, interaction: discord.Interaction, server_id: str):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        # Get translator for localization
        translator = None
        if interaction.guild:
            try:
                translator = await get_translator(str(interaction.guild.id), self.data_service)
            except:
                pass
        
        if await self.data_service.remove_from_blacklist(server_id):
            await self.data_service.save_blacklist()
            from src.components.admin import BlacklistRemoveSuccessView
            view = BlacklistRemoveSuccessView(server_id, translator=translator)
            await interaction.followup.send(view=view)
        else:
            from src.components.admin import BlacklistRemoveNotFoundView
            view = BlacklistRemoveNotFoundView(server_id, translator=translator)
            await interaction.followup.send(view=view)

    @blacklist_group.command(
        name="check", 
        description=get_command_description("admin.blacklist.check"),
        auto_locale_strings=False
    )
    @app_commands.describe(server_id="Server ID to check blacklist status")
    async def blacklist_check(self, interaction: discord.Interaction, server_id: str):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        blacklist_entries = await self.data_service.get_blacklist_entries()
        
        if server_id not in blacklist_entries:
            from src.components.admin import BlacklistCheckNotFoundView
            view = BlacklistCheckNotFoundView(server_id)
            await interaction.followup.send(view=view)
            return
        
        entry = blacklist_entries[server_id]
        guild = self.bot.get_guild(int(server_id))
        server_name = guild.name if guild else (entry.server_name or "Unknown")
        
        from src.components.admin import BlacklistCheckFoundView
        view = BlacklistCheckFoundView(server_id, server_name, entry)
        await interaction.followup.send(view=view)

    @app_commands.command(
        name="recache",
        description=get_command_description("admin.recache"),
        auto_locale_strings=False
    )
    async def recache(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        try:
            await self.data_service.reload_all_caches()
            await self.data_service.reload_timezones_cache()
            
            servers_count = len(self.data_service._servers_cache)
            blacklist_count = len(self.data_service._blacklist_cache)
            channels_count = sum(len(s.channels) for s in self.data_service._servers_cache.values())
            timezone_count = len(self.data_service._timezones_cache)
            
            from src.components.admin import RecacheSuccessView
            view = RecacheSuccessView(
                cache_type="All data (except config)",
                servers=servers_count,
                blacklist=blacklist_count,
                channels=channels_count,
                timezones=timezone_count
            )
            await interaction.followup.send(view=view)
            
        except Exception as e:
            from src.components.admin import RecacheErrorView
            view = RecacheErrorView("all", str(e))
            await interaction.followup.send(view=view)

    @error_group.command(
        name="check", 
        description=get_command_description("admin.error.check"),
        auto_locale_strings=False
    )
    @app_commands.describe(error_id="The error ID to check")
    async def error_check(self, interaction: discord.Interaction, error_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        error_doc = await logger.get_error(error_id)
        
        if not error_doc:
            from src.components.admin import ErrorNotFoundView
            view = ErrorNotFoundView(error_id)
            await interaction.followup.send(view=view)
            return
        
        # Error details display
        from src.components.admin import ErrorDetailsView
        
        view = ErrorDetailsView(error_doc, self.bot)
        await interaction.followup.send(view=view)

    @error_group.command(
        name="delete", 
        description=get_command_description("admin.error.delete"),
        auto_locale_strings=False
    )
    @app_commands.describe(error_id="The error ID to delete")
    async def error_delete(self, interaction: discord.Interaction, error_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        success = await logger.delete_error(error_id)
        
        if success:
            from src.components.admin import ErrorDeleteSuccessView
            view = ErrorDeleteSuccessView(error_id)
            await interaction.followup.send(view=view)
        else:
            from src.components.admin import ErrorDeleteFailedView
            view = ErrorDeleteFailedView(error_id)
            await interaction.followup.send(view=view)

    @error_group.command(
        name="list", 
        description=get_command_description("admin.error.list"),
        auto_locale_strings=False
    )
    @app_commands.describe(limit="Number of errors to show (default: 10, max: 25)")
    async def error_list(self, interaction: discord.Interaction, limit: int = 10):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        limit = min(max(1, limit), 25)
        errors = await logger.get_recent_errors(limit)
        
        if not errors:
            from src.components.admin import NoErrorsView
            view = NoErrorsView()
            await interaction.followup.send(view=view)
            return
        
        # Error list display
        from src.components.admin import ErrorListView
        
        view = ErrorListView(errors)
        await interaction.followup.send(view=view)

    @error_group.command(
        name="clear", 
        description=get_command_description("admin.error.clear"),
        auto_locale_strings=False
    )
    async def error_clear(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return
        
        from src.services.database_connection_manager import db_manager
        
        try:
            errors_collection = db_manager.db.errors
            result = await errors_collection.delete_many({})
            from src.components.admin import ErrorsClearedView
            view = ErrorsClearedView(result.deleted_count)
            await interaction.followup.send(view=view)
        except Exception as e:
            error_id = await logger.log_error(
                LogArea.DATABASE,
                "Failed to clear errors from database",
                exception=e
            )
            from src.components.admin import ErrorsClearFailedView
            view = ErrorsClearFailedView(error_id)
            await interaction.followup.send(view=view)


    @force_group.command(
        name="remove_server", 
        description=get_command_description("admin.force.remove_server"),
        auto_locale_strings=False
    )
    @app_commands.describe(id="Server ID to remove all subscriptions from")
    async def force_remove_server(self, interaction: discord.Interaction, id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return

        servers = await self.data_service.get_all_servers()

        if id not in servers:
            from src.components.admin import ForceUnsubNotFoundView
            view = ForceUnsubNotFoundView(id)
            await interaction.followup.send(view=view)
            return

        server = servers[id]
        channels_removed = len(server.channels)

        for channel_id in list(server.channels.keys()):
            self.scheduler_service.remove_channel_clear_job(id, channel_id)
            server.remove_channel(channel_id)

        await self.data_service.save_servers()

        from src.components.admin import ForceUnsubSuccessView
        view = ForceUnsubSuccessView("server", id, channels_removed)
        await interaction.followup.send(view=view)

    @force_group.command(
        name="remove_channel", 
        description=get_command_description("admin.force.remove_channel"),
        auto_locale_strings=False
    )
    @app_commands.describe(id="Channel ID to unsubscribe")
    async def force_remove_channel(self, interaction: discord.Interaction, id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not await self._check_admin_permission_before_defer(interaction):
            return

        servers = await self.data_service.get_all_servers()

        for server_id, server in servers.items():
            if id in server.channels:
                self.scheduler_service.remove_channel_clear_job(server_id, id)
                server.remove_channel(id)
                await self.data_service.save_servers()

                from src.components.admin import ForceUnsubSuccessView
                view = ForceUnsubSuccessView("channel", id, server_id=server_id)
                await interaction.followup.send(view=view)
                return

        from src.components.admin import ForceUnsubNotFoundView
        view = ForceUnsubNotFoundView(id)
        await interaction.followup.send(view=view)


async def setup(bot):
    if bot.config.guild_id:
        await bot.add_cog(AdminCommands(bot), guild=discord.Object(id=bot.config.guild_id))
