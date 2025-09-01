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
            await interaction.response.send_message(
                "❌ This command is restricted to the bot owner.", ephemeral=True
            )
            return False
        return True
    
    @app_commands.command(
        name="cache_stats", description="View cache statistics and performance"
    )
    async def cache_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        # Get cache statistics
        cache_stats = self.data_service.get_cache_stats()
        
        # Use Components v2 for cache stats display
        from src.components.owner import CacheStatsView
        
        view = CacheStatsView(cache_stats)
        await interaction.followup.send(view=view)

    @app_commands.command(
        name="list", description="List all servers and their subscribed channels"
    )
    async def list_servers(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        servers = await self.data_service.get_all_servers()

        if not servers:
            await interaction.followup.send("No servers have subscribed channels.")
            return

        # Use Components v2 for server list display
        from src.components.owner import ServerListView
        
        view = ServerListView(servers, self.bot)
        await interaction.followup.send(view=view)

    @app_commands.command(
        name="force_unsub", description="Force unsubscribe a server or channel"
    )
    @app_commands.describe(target_id="Server ID or Channel ID to unsubscribe")
    async def force_unsub(self, interaction: discord.Interaction, target_id: str):
        await interaction.response.defer(thinking=True)

        # Try to determine if it's a server or channel
        servers = await self.data_service.get_all_servers()

        # Check if it's a server ID
        if target_id in servers:
            server = servers[target_id]
            channels_removed = len(server.channels)

            # Remove all jobs and channels for this server
            for channel_id in list(server.channels.keys()):
                self.scheduler_service.remove_channel_clear_job(target_id, channel_id)
                server.remove_channel(channel_id)

            # Keep server in database even with no channels
            await self.data_service.save_servers()

            await interaction.followup.send(
                f"✅ Cleared {channels_removed} subscribed channels from server {target_id}."
            )
            return

        # Check if it's a channel ID in any server
        for server_id, server in servers.items():
            if target_id in server.channels:
                # Remove job
                self.scheduler_service.remove_channel_clear_job(server_id, target_id)

                # Remove from data service
                server.remove_channel(target_id)
                await self.data_service.save_servers()

                await interaction.followup.send(
                    f"✅ Removed channel {target_id} from server {server_id}."
                )
                return

        await interaction.followup.send(
            f"❌ No server or channel found with ID: {target_id}"
        )

    @app_commands.command(
        name="blacklist_add", description="Add a server to the blacklist"
    )
    @app_commands.describe(server_id="Server ID to blacklist")
    async def blacklist_add(self, interaction: discord.Interaction, server_id: str):
        # Try to get the server name if the bot is in the server
        guild = self.bot.get_guild(int(server_id))
        server_name = guild.name if guild else "Unknown"
        
        if await self.data_service.add_to_blacklist(server_id, server_name):
            await self.data_service.save_blacklist()

            # Remove any existing subscriptions but keep server in database
            server = await self.data_service.get_server(server_id)
            if server:
                for channel_id in list(server.channels.keys()):
                    self.scheduler_service.remove_channel_clear_job(server_id, channel_id)
                    server.remove_channel(channel_id)
                # Keep server in database even with no channels
                await self.data_service.save_servers()

            await interaction.response.send_message(
                f"✅ Added server {server_name} ({server_id}) to blacklist and removed all subscriptions."
            )
        else:
            await interaction.response.send_message(
                f"❌ Server {server_id} is already blacklisted.", ephemeral=True
            )

    @app_commands.command(
        name="blacklist_remove", description="Remove a server from the blacklist"
    )
    @app_commands.describe(server_id="Server ID to remove from blacklist")
    async def blacklist_remove(self, interaction: discord.Interaction, server_id: str):
        if await self.data_service.remove_from_blacklist(server_id):
            await self.data_service.save_blacklist()
            await interaction.response.send_message(
                f"✅ Removed server {server_id} from blacklist."
            )
        else:
            await interaction.response.send_message(
                f"❌ Server {server_id} is not blacklisted.", ephemeral=True
            )

    @app_commands.command(
        name="blacklist_list", description="List all blacklisted servers"
    )
    async def blacklist_list(self, interaction: discord.Interaction):
        blacklist_with_names = await self.data_service.get_blacklist_with_names()

        if not blacklist_with_names:
            await interaction.response.send_message(
                "No servers are currently blacklisted."
            )
            return

        # Use Components v2 for blacklist display
        from src.components.owner import BlacklistView
        
        view = BlacklistView(blacklist_with_names, self.bot)
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
            self.data_service._timezones_cache.clear()
            
            # Mark as uninitialized to force reload
            self.data_service._initialized = False
            
            # Reinitialize to reload from database
            await self.data_service.initialize()
            
            # Get stats after reload
            servers_count = len(self.data_service._servers_cache)
            blacklist_count = len(self.data_service._blacklist_cache)
            timezones_count = len(self.data_service._timezones_cache)
            
            # Use Components v2 for cache reload display
            from src.components.owner import CacheReloadView
            
            view = CacheReloadView(servers_count, blacklist_count, timezones_count)
            await interaction.followup.send(view=view)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error reloading cache: {e}")

    @app_commands.command(name="stats", description="Show bot statistics")
    async def stats(self, interaction: discord.Interaction):
        servers = await self.data_service.get_all_servers()
        blacklist = await self.data_service.get_blacklist()
        jobs = self.scheduler_service.get_all_jobs()

        # Use Components v2 for stats display
        from src.components.owner import StatsView
        
        view = StatsView(self.bot, servers, blacklist, jobs)
        await interaction.response.send_message(view=view)

    @app_commands.command(
        name="error_lookup", description="Look up an error by its ID"
    )
    @app_commands.describe(error_id="The error ID to look up")
    async def error_lookup(self, interaction: discord.Interaction, error_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        # Get error from database
        error_doc = await logger.get_error(error_id)
        
        if not error_doc:
            await interaction.followup.send(f"❌ No error found with ID: `{error_id}`")
            return
        
        # Use Components v2 for error details display
        from src.components.owner import ErrorDetailsView
        
        view = ErrorDetailsView(error_doc, self.bot)
        await interaction.followup.send(view=view)

    @app_commands.command(
        name="error_delete", description="Delete an error by its ID"
    )
    @app_commands.describe(error_id="The error ID to delete")
    async def error_delete(self, interaction: discord.Interaction, error_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        # Delete error from database
        success = await logger.delete_error(error_id)
        
        if success:
            await interaction.followup.send(f"✅ Error `{error_id}` has been deleted.")
        else:
            await interaction.followup.send(f"❌ Could not delete error `{error_id}`. It may not exist.")

    @app_commands.command(
        name="error_list", description="List recent errors"
    )
    @app_commands.describe(limit="Number of errors to show (default: 10, max: 25)")
    async def error_list(self, interaction: discord.Interaction, limit: int = 10):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        # Validate limit
        limit = min(max(1, limit), 25)
        
        # Get recent errors
        errors = await logger.get_recent_errors(limit)
        
        if not errors:
            await interaction.followup.send("No errors found in the database.")
            return
        
        # Use Components v2 for error list display
        from src.components.owner import ErrorListView
        
        view = ErrorListView(errors)
        await interaction.followup.send(view=view)

    @app_commands.command(
        name="error_clear", description="Clear all errors from the database"
    )
    async def error_clear(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        from src.services.database_connection_manager import db_manager
        
        try:
            errors_collection = db_manager.db.errors
            result = await errors_collection.delete_many({})
            await interaction.followup.send(f"✅ Cleared {result.deleted_count} errors from the database.")
        except Exception as e:
            error_id = await logger.log_error(
                LogArea.DATABASE,
                "Failed to clear errors from database",
                exception=e
            )
            await interaction.followup.send(f"❌ Failed to clear errors. Error ID: `{error_id}`")


async def setup(bot):
    if bot.config.is_owner_mode and bot.config.guild_id:
        await bot.add_cog(
            OwnerCommands(bot), guild=discord.Object(id=bot.config.guild_id)
        )
