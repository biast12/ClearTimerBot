import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


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

    @app_commands.command(name="reload", description="Reload all bot commands")
    async def reload_commands(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            # Reload all extensions
            extensions = list(self.bot.extensions.keys())
            for ext in extensions:
                await self.bot.reload_extension(ext)

            # Register commands with Discord
            await self.bot.tree.sync()

            await interaction.followup.send("✅ Successfully reloaded and registered all commands.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error reloading commands: {e}")

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
        name="removed_servers", description="Show servers the bot has been removed from"
    )
    async def removed_servers(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        from src.services.database import db_manager

        removed_servers_collection = db_manager.removed_servers
        removed_servers = await removed_servers_collection.find().to_list(None)

        if not removed_servers:
            await interaction.followup.send("No servers in removal tracking.")
            return

        embed = discord.Embed(
            title="📤 Removed Servers",
            description="Servers the bot has been removed from",
            color=discord.Color.orange(),
        )

        server_list = []
        now = datetime.now(timezone.utc)

        for server_doc in removed_servers:
            server_id = server_doc["_id"]
            server_name = server_doc.get("server_name", "Unknown")
            removed_at = server_doc.get("removed_at")
            member_count = server_doc.get("member_count", 0)

            if removed_at:
                days_ago = (now - removed_at).days
                if days_ago == 0:
                    time_str = "Today"
                elif days_ago == 1:
                    time_str = "1 day ago"
                else:
                    time_str = f"{days_ago} days ago"
            else:
                time_str = "Unknown"

            server_list.append(
                f"• {server_name} ({server_id})\n  Removed: {time_str} | Members: {member_count}"
            )

        # Split into chunks if needed
        chunk_size = 10
        for i in range(0, len(server_list), chunk_size):
            chunk = server_list[i : i + chunk_size]
            field_name = "Servers" if i == 0 else "Servers (continued)"
            embed.add_field(name=field_name, value="\n".join(chunk), inline=False)

        embed.set_footer(
            text=f"Total: {len(removed_servers)} servers | "
            f"Servers removed >30 days ago will be auto-cleaned"
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="cleanup_removed",
        description="Manually cleanup servers removed >30 days ago",
    )
    async def cleanup_removed(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            cleaned_count = await self.data_service.cleanup_old_removed_servers()

            if cleaned_count > 0:
                await interaction.followup.send(
                    f"✅ Successfully cleaned up {cleaned_count} server(s) that were removed more than 30 days ago."
                )
            else:
                await interaction.followup.send(
                    "No servers needed cleanup. All removed servers are less than 30 days old."
                )
        except Exception as e:
            await interaction.followup.send(f"❌ Error during cleanup: {e}")


async def setup(bot):
    if bot.config.is_owner_mode and bot.config.guild_id:
        await bot.add_cog(
            OwnerCommands(bot), guild=discord.Object(id=bot.config.guild_id)
        )
