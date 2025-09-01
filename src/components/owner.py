"""
Discord Components v2 for Owner Commands
"""

import discord
from discord.ext import commands
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class ServerListView(discord.ui.LayoutView):
    """View for listing servers using Components v2"""
    
    def __init__(self, servers: dict, bot):
        super().__init__()
        
        content = "📋 **Subscribed Servers and Channels**\n\n"
        
        field_count = 0
        total_servers = len(servers)
        total_channels = sum(len(s.channels) for s in servers.values())
        
        for server_id, server in list(servers.items())[:10]:  # Show first 10
            if not server.channels:
                continue
            
            # Get guild name
            guild = bot.get_guild(int(server_id))
            guild_name = guild.name if guild else f"Unknown ({server.server_name})"
            
            content += f"**{guild_name}** ({server_id})\n"
            
            # Build channel list
            for channel_id, timer_data in list(server.channels.items())[:5]:
                channel = bot.get_channel(int(channel_id))
                channel_name = channel.name if channel else "Unknown"
                content += f"• #{channel_name} ({timer_data.timer})\n"
            
            if len(server.channels) > 5:
                content += f"... and {len(server.channels) - 5} more channels\n"
            
            content += "\n"
            field_count += 1
            
            if field_count >= 10:
                break
        
        if total_servers > 10:
            content += f"... and {total_servers - 10} more servers\n\n"
        
        content += f"_Total: {total_servers} servers, {total_channels} channels_"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class BlacklistView(discord.ui.LayoutView):
    """View for blacklist display using Components v2"""
    
    def __init__(self, blacklist_with_names: dict, bot):
        super().__init__()
        
        content = "🚫 **Blacklisted Servers**\n\n"
        
        server_list = []
        for server_id, stored_name in blacklist_with_names.items():
            # Try to get current name from bot's cache, fallback to stored name
            guild = bot.get_guild(int(server_id))
            guild_name = guild.name if guild else (stored_name or "Unknown")
            server_list.append(f"• {guild_name} ({server_id})")
        
        # Show first 20
        content += "\n".join(server_list[:20])
        
        if len(server_list) > 20:
            content += f"\n... and {len(server_list) - 20} more\n"
        
        content += f"\n\n_Total: {len(blacklist_with_names)} servers_"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class CacheReloadView(discord.ui.LayoutView):
    """View for cache reload confirmation using Components v2"""
    
    def __init__(self, servers_count: int, blacklist_count: int, timezones_count: int):
        super().__init__()
        
        content = (
            "🔄 **Cache Reloaded**\n\n"
            "All caches have been cleared and reloaded from the database.\n\n"
            "**📊 Loaded Data**\n"
            f"• Servers: {servers_count}\n"
            f"• Blacklisted: {blacklist_count}\n"
            f"• Timezones: {timezones_count}\n\n"
            "_Cache reload successful_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class ErrorDetailsView(discord.ui.LayoutView):
    """View for error details using Components v2"""
    
    def __init__(self, error_doc, bot):
        super().__init__()
        
        timestamp = int(error_doc.timestamp.timestamp())
        
        content = f"**Error Details: {error_doc.error_id}**\n\n"
        content += f"**Level:** {error_doc.level}\n"
        content += f"**Area:** {error_doc.area}\n"
        content += f"**Time:** <t:{timestamp}:F>\n\n"
        
        # Add message field
        message = error_doc.message
        if len(message) > 500:
            message = message[:497] + "..."
        content += f"**Message:** {message}\n\n"
        
        # Add context fields if present
        if error_doc.guild_id:
            guild = bot.get_guild(int(error_doc.guild_id))
            guild_name = guild.name if guild else "Unknown"
            content += f"**Server:** {guild_name} ({error_doc.guild_id})\n"
        
        if error_doc.channel_id:
            channel = bot.get_channel(int(error_doc.channel_id))
            channel_name = channel.name if channel else "Unknown"
            content += f"**Channel:** {channel_name} ({error_doc.channel_id})\n"
        
        if error_doc.user_id:
            content += f"**User:** <@{error_doc.user_id}> ({error_doc.user_id})\n"
        
        if error_doc.command:
            content += f"**Command:** {error_doc.command}\n"
        
        # Add traceback if present (truncate if too long)
        if error_doc.stack_trace:
            tb = error_doc.stack_trace
            if len(tb) > 800:
                tb = tb[:797] + "..."
            content += f"\n**Traceback:**\n```python\n{tb}\n```"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ErrorListView(discord.ui.LayoutView):
    """View for error list using Components v2"""
    
    def __init__(self, errors: list):
        super().__init__()
        
        content = f"**Recent Errors** (Last {len(errors)})\n\n"
        
        for error in errors[:10]:  # Show first 10
            timestamp = f"<t:{int(error.timestamp.timestamp())}:R>"
            message = error.message
            if len(message) > 50:
                message = message[:47] + "..."
            
            content += (
                f"**ID:** `{error.error_id}` | {error.level}\n"
                f"**Area:** {error.area}\n"
                f"**Time:** {timestamp}\n"
                f"**Message:** {message}\n"
                f"---\n"
            )
        
        if len(errors) > 10:
            content += f"\n... and {len(errors) - 10} more errors\n"
        
        content += f"\n_Use `/owner error_lookup <id>` to see full details_"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)


class StatsView(discord.ui.LayoutView):
    """View for bot statistics using Components v2"""
    
    def __init__(self, bot: commands.Bot, servers: dict, blacklist: set, jobs: list):
        super().__init__()
        
        content = (
            f"📊 **Bot Statistics**\n\n"
            f"**Servers**\n"
            f"Connected: {len(bot.guilds)}\n"
            f"Subscribed: {len(servers)}\n\n"
            f"**Channels**\n"
            f"Total Subscribed: {sum(len(s.channels) for s in servers.values())}\n\n"
            f"**Jobs**\n"
            f"Active: {len(jobs)}\n\n"
            f"**Blacklist**\n"
            f"Servers: {len(blacklist)}\n\n"
            f"**Latency**\n"
            f"{round(bot.latency * 1000)}ms"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class CacheStatsView(discord.ui.LayoutView):
    """View for cache statistics using Components v2"""
    
    def __init__(self, cache_stats: dict):
        super().__init__()
        
        memory_stats = cache_stats.get("memory", {})
        warm_stats = cache_stats.get("warm", {})
        cold_stats = cache_stats.get("cold", {})
        
        # Calculate overall stats
        total_hits = memory_stats.get('hits', 0) + warm_stats.get('hits', 0) + cold_stats.get('hits', 0)
        total_misses = memory_stats.get('misses', 0) + warm_stats.get('misses', 0) + cold_stats.get('misses', 0)
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        content = (
            f"📊 **Cache Statistics**\n\n"
            f"**🔥 Memory Cache (Hot Data)**\n"
            f"Hit Rate: {memory_stats.get('hit_rate', 0)}%\n"
            f"Hits: {memory_stats.get('hits', 0)}\n"
            f"Misses: {memory_stats.get('misses', 0)}\n"
            f"Cached Items: {memory_stats.get('cached_items', 0)}\n"
            f"Evictions: {memory_stats.get('evictions', 0)}\n\n"
            f"**🌡️ Warm Cache**\n"
            f"Hit Rate: {warm_stats.get('hit_rate', 0)}%\n"
            f"Hits: {warm_stats.get('hits', 0)}\n"
            f"Misses: {warm_stats.get('misses', 0)}\n"
            f"Cached Items: {warm_stats.get('cached_items', 0)}\n"
            f"Evictions: {warm_stats.get('evictions', 0)}\n\n"
            f"**❄️ Cold Cache**\n"
            f"Hit Rate: {cold_stats.get('hit_rate', 0)}%\n"
            f"Hits: {cold_stats.get('hits', 0)}\n"
            f"Misses: {cold_stats.get('misses', 0)}\n"
            f"Cached Items: {cold_stats.get('cached_items', 0)}\n"
            f"Evictions: {cold_stats.get('evictions', 0)}\n\n"
            f"**📈 Overall Performance**\n"
            f"Total Requests: {total_requests}\n"
            f"Overall Hit Rate: {overall_hit_rate:.2f}%\n"
            f"Database Calls Saved: {total_hits}\n\n"
            f"_Cache helps reduce database load and improve response times_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)