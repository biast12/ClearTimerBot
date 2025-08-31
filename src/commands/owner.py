import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
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
        
        embed = discord.Embed(
            title="📊 Cache Statistics",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Memory cache stats
        memory_stats = cache_stats.get("memory", {})
        embed.add_field(
            name="🔥 Memory Cache (Hot Data)",
            value=(
                f"**Hit Rate:** {memory_stats.get('hit_rate', 0)}%\n"
                f"**Hits:** {memory_stats.get('hits', 0)}\n"
                f"**Misses:** {memory_stats.get('misses', 0)}\n"
                f"**Cached Items:** {memory_stats.get('cached_items', 0)}\n"
                f"**Evictions:** {memory_stats.get('evictions', 0)}"
            ),
            inline=True
        )
        
        # Warm cache stats
        warm_stats = cache_stats.get("warm", {})
        embed.add_field(
            name="🌡️ Warm Cache",
            value=(
                f"**Hit Rate:** {warm_stats.get('hit_rate', 0)}%\n"
                f"**Hits:** {warm_stats.get('hits', 0)}\n"
                f"**Misses:** {warm_stats.get('misses', 0)}\n"
                f"**Cached Items:** {warm_stats.get('cached_items', 0)}\n"
                f"**Evictions:** {warm_stats.get('evictions', 0)}"
            ),
            inline=True
        )
        
        # Cold cache stats
        cold_stats = cache_stats.get("cold", {})
        embed.add_field(
            name="❄️ Cold Cache",
            value=(
                f"**Hit Rate:** {cold_stats.get('hit_rate', 0)}%\n"
                f"**Hits:** {cold_stats.get('hits', 0)}\n"
                f"**Misses:** {cold_stats.get('misses', 0)}\n"
                f"**Cached Items:** {cold_stats.get('cached_items', 0)}\n"
                f"**Evictions:** {cold_stats.get('evictions', 0)}"
            ),
            inline=True
        )
        
        # Calculate overall stats
        total_hits = memory_stats.get('hits', 0) + warm_stats.get('hits', 0) + cold_stats.get('hits', 0)
        total_misses = memory_stats.get('misses', 0) + warm_stats.get('misses', 0) + cold_stats.get('misses', 0)
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        embed.add_field(
            name="📈 Overall Performance",
            value=(
                f"**Total Requests:** {total_requests}\n"
                f"**Overall Hit Rate:** {overall_hit_rate:.2f}%\n"
                f"**Database Calls Saved:** {total_hits}"
            ),
            inline=False
        )
        
        embed.set_footer(text="Cache helps reduce database load and improve response times")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="list", description="List all servers and their subscribed channels"
    )
    async def list_servers(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        servers = await self.data_service.get_all_servers()

        if not servers:
            await interaction.followup.send("No servers have subscribed channels.")
            return

        embeds = []
        current_embed = discord.Embed(
            title="📋 Subscribed Servers and Channels", color=discord.Color.blue()
        )

        field_count = 0

        for server_id, server in servers.items():
            if not server.channels:
                continue

            # Get guild name
            guild = self.bot.get_guild(int(server_id))
            guild_name = guild.name if guild else f"Unknown ({server.server_name})"

            # Build channel list
            channel_list = []
            for channel_id, timer_data in server.channels.items():
                channel = self.bot.get_channel(int(channel_id))
                channel_name = channel.name if channel else "Unknown"
                channel_list.append(f"• #{channel_name} ({timer_data.timer})")

            field_value = "\n".join(channel_list[:10])
            if len(channel_list) > 10:
                field_value += f"\n... and {len(channel_list) - 10} more"

            # Add field to embed
            current_embed.add_field(
                name=f"{guild_name} ({server_id})", value=field_value, inline=False
            )

            field_count += 1

            # Create new embed if current one is full
            if field_count >= 10:
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title="📋 Subscribed Servers and Channels (continued)",
                    color=discord.Color.blue(),
                )
                field_count = 0

        if field_count > 0:
            embeds.append(current_embed)

        # Add statistics to the last embed
        total_servers = len(servers)
        total_channels = sum(len(s.channels) for s in servers.values())

        embeds[-1].set_footer(
            text=f"Total: {total_servers} servers, {total_channels} channels"
        )

        await interaction.followup.send(embeds=embeds)

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
                self.scheduler_service.remove_job(target_id, channel_id)
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
                self.scheduler_service.remove_job(server_id, target_id)

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
                    self.scheduler_service.remove_job(server_id, channel_id)
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

        embed = discord.Embed(title="🚫 Blacklisted Servers", color=discord.Color.red())

        server_list = []
        for server_id, stored_name in blacklist_with_names.items():
            # Try to get current name from bot's cache, fallback to stored name
            guild = self.bot.get_guild(int(server_id))
            guild_name = guild.name if guild else (stored_name or "Unknown")
            server_list.append(f"• {guild_name} ({server_id})")

        # Split into chunks if needed
        chunk_size = 20
        for i in range(0, len(server_list), chunk_size):
            chunk = server_list[i : i + chunk_size]
            field_name = "Servers" if i == 0 else "Servers (continued)"
            embed.add_field(name=field_name, value="\n".join(chunk), inline=False)

        embed.set_footer(text=f"Total: {len(blacklist_with_names)} servers")

        await interaction.response.send_message(embed=embed)

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
            
            embed = discord.Embed(
                title="🔄 Cache Reloaded",
                description="All caches have been cleared and reloaded from the database.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📊 Loaded Data",
                value=(
                    f"**Servers:** {servers_count}\n"
                    f"**Blacklisted:** {blacklist_count}\n"
                    f"**Timezones:** {timezones_count}"
                ),
                inline=False
            )
            
            embed.set_footer(text="Cache reload successful")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error reloading cache: {e}")

    @app_commands.command(name="stats", description="Show bot statistics")
    async def stats(self, interaction: discord.Interaction):
        servers = await self.data_service.get_all_servers()
        blacklist = await self.data_service.get_blacklist()
        jobs = self.scheduler_service.get_all_jobs()

        embed = discord.Embed(title="📊 Bot Statistics", color=discord.Color.blue())

        embed.add_field(
            name="Servers",
            value=f"Connected: {len(self.bot.guilds)}\nSubscribed: {len(servers)}",
            inline=True,
        )

        embed.add_field(
            name="Channels",
            value=f"Total Subscribed: {sum(len(s.channels) for s in servers.values())}",
            inline=True,
        )

        embed.add_field(name="Jobs", value=f"Active: {len(jobs)}", inline=True)

        embed.add_field(
            name="Blacklist", value=f"Servers: {len(blacklist)}", inline=True
        )

        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True
        )

        await interaction.response.send_message(embed=embed)

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
        
        # Create embed with error details
        embed = discord.Embed(
            title=f"Error Details: {error_id}",
            color=discord.Color.red(),
            timestamp=error_doc["timestamp"]
        )
        
        embed.add_field(name="Level", value=str(error_doc["level"]), inline=True)
        embed.add_field(name="Area", value=str(error_doc["area"]), inline=True)
        
        embed.add_field(name="Time", value=f"<t:{int(error_doc['timestamp'].timestamp())}:F>", inline=True)
        
        # Truncate message field to Discord's limit
        message = error_doc["message"]
        if len(message) > 1024:
            message = message[:1021] + "..."
        embed.add_field(name="Message", value=message, inline=False)
        
        # Add context fields if present
        if error_doc.get("server_id"):
            guild = self.bot.get_guild(int(error_doc["server_id"]))
            guild_name = guild.name if guild else "Unknown"
            embed.add_field(name="Server", value=f"{guild_name} ({error_doc['server_id']})", inline=True)
        
        if error_doc.get("channel_id"):
            channel = self.bot.get_channel(int(error_doc["channel_id"]))
            channel_name = channel.name if channel else "Unknown"
            embed.add_field(name="Channel", value=f"{channel_name} ({error_doc['channel_id']})", inline=True)
        
        if error_doc.get("user_id"):
            embed.add_field(name="User", value=f"<@{error_doc['user_id']}> ({error_doc['user_id']})", inline=True)
        
        if error_doc.get("command"):
            embed.add_field(name="Command", value=error_doc["command"], inline=True)
        
        # Add traceback if present (truncate if too long)
        if error_doc.get("traceback"):
            tb = error_doc["traceback"]
            # Account for code block formatting when truncating
            formatted_tb = f"```python\n{tb}```"
            if len(formatted_tb) > 1024:
                # Subtract length of formatting characters
                max_tb_length = 1024 - len("```python\n```") - 3  # -3 for "..."
                tb = tb[:max_tb_length] + "..."
                formatted_tb = f"```python\n{tb}```"
            embed.add_field(name="Traceback", value=formatted_tb, inline=False)
        
        # Add additional data if present
        if error_doc.get("additional_data"):
            data_str = "\n".join([f"**{k}:** {v}" for k, v in error_doc["additional_data"].items()])
            if len(data_str) > 1024:
                data_str = data_str[:1021] + "..."
            embed.add_field(name="Additional Data", value=data_str, inline=False)
        
        await interaction.followup.send(embed=embed)

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
        
        # Create embed with error list
        embed = discord.Embed(
            title=f"Recent Errors (Last {len(errors)})",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        
        for error in errors:
            timestamp = f"<t:{int(error['timestamp'].timestamp())}:R>"
            message = error['message']
            if len(message) > 50:
                message = message[:47] + "..."
            
            field_value = f"**Area:** {error['area']}\n**Time:** {timestamp}\n**Message:** {message}"
            embed.add_field(
                name=f"ID: {error['_id']} | {error['level']}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text=f"Use /owner error_lookup <id> to see full details")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="error_clear", description="Clear all errors from the database"
    )
    async def error_clear(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        from src.services.database import db_manager
        
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
