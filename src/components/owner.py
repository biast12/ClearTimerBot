"""
View Display for Owner Commands
"""

import discord
from discord.ext import commands


class SimpleStatsView(discord.ui.LayoutView):
    """View for showing simple bot statistics"""
    
    def __init__(self, total_servers: int, total_channels: int, removed_servers: int, 
                 blacklisted_servers: int, error_count: int):
        super().__init__()
        
        content = "📊 **Bot Statistics**\n\n"
        content += f"**Servers:** {total_servers}\n"
        content += f"**Subscribed Channels:** {total_channels}\n"
        content += f"**Removed Servers:** {removed_servers}\n"
        content += f"**Blacklisted Servers:** {blacklisted_servers}\n"
        content += f"**Saved Errors:** {error_count}"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class ServerStatsView(discord.ui.LayoutView):
    """View for showing server-specific statistics"""
    
    def __init__(self, server_id: str, server_name: str, channel_count: int,
                 is_blacklisted: bool, error_count: int, bot, channels: dict):
        super().__init__()
        
        content = f"📊 **Server Statistics**\n\n"
        content += f"**Server:** {server_name}\n"
        content += f"**Server ID:** {server_id}\n"
        content += f"**Subscribed Channels:** {channel_count}\n"
        content += f"**Blacklisted:** {'Yes ⛔' if is_blacklisted else 'No ✅'}\n"
        content += f"**Errors:** {error_count}\n"
        
        if channels:
            content += f"\n**Channels:**\n"
            for channel_id, timer_data in list(channels.items())[:10]:
                channel = bot.get_channel(int(channel_id))
                channel_name = f"#{channel.name}" if channel else "Unknown Channel"
                content += f"• {channel_name} - `{timer_data.timer}`\n"
            
            if len(channels) > 10:
                content += f"_... and {len(channels) - 10} more channels_"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value if is_blacklisted else discord.Color.blue().value
        )
        self.add_item(container)


class ServerNotFoundView(discord.ui.LayoutView):
    """View for when a server is not found in the database"""
    
    def __init__(self, server_id: str):
        super().__init__()
        
        content = f"❌ **Server Not Found**\n\n"
        content += f"Server ID `{server_id}` was not found in the database.\n"
        content += f"This server has never been subscribed to the bot."
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ServerListView(discord.ui.LayoutView):
    """View for listing servers"""
    
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



class CacheReloadView(discord.ui.LayoutView):
    """View for cache reload confirmation"""
    
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
    """View for error details"""
    
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
    """View for error list"""
    
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
        
        content += f"\n_Use `/owner error check <id>` to see full details_"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)


class StatsView(discord.ui.LayoutView):
    """View for bot statistics"""
    
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
    """View for cache statistics"""
    
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


class NoServersView(discord.ui.LayoutView):
    """View for no servers message"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "ℹ️ **No Subscribed Channels**\n\n"
            "No servers have subscribed channels yet.\n\n"
            "_Servers can subscribe channels using `/subscription add`_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.greyple().value
        )
        self.add_item(container)


class ForceUnsubSuccessView(discord.ui.LayoutView):
    """View for force unsubscribe success"""
    
    def __init__(self, target_type: str, target_id: str, count: int = None, server_id: str = None):
        super().__init__()
        
        if target_type == "server":
            content = (
                f"✅ **Server Unsubscribed**\n\n"
                f"Cleared {count} subscribed channel{'s' if count != 1 else ''} from server `{target_id}`.\n\n"
                f"_The server can subscribe channels again using `/subscription add`_"
            )
        else:  # channel
            content = (
                f"✅ **Channel Unsubscribed**\n\n"
                f"Removed channel `{target_id}` from server `{server_id}`.\n\n"
                f"_The channel can be subscribed again using `/subscription add`_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class ForceUnsubNotFoundView(discord.ui.LayoutView):
    """View for force unsubscribe not found"""
    
    def __init__(self, target_id: str):
        super().__init__()
        
        content = (
            f"❌ **Not Found**\n\n"
            f"No server or channel found with ID: `{target_id}`\n\n"
            f"_Please check the ID and try again_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class BlacklistAddSuccessView(discord.ui.LayoutView):
    """View for blacklist add success"""
    
    def __init__(self, server_name: str, server_id: str, reason: str = "No reason provided"):
        super().__init__()
        
        content = (
            f"✅ **Server Blacklisted**\n\n"
            f"Added server **{server_name}** (`{server_id}`) to blacklist.\n\n"
            f"📝 **Reason:** {reason}\n\n"
            f"• All subscriptions have been removed\n"
            f"• The server cannot use bot commands"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class BlacklistAddAlreadyView(discord.ui.LayoutView):
    """View for server already blacklisted"""
    
    def __init__(self, server_id: str):
        super().__init__()
        
        content = (
            f"❌ **Already Blacklisted**\n\n"
            f"Server `{server_id}` is already blacklisted."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class BlacklistRemoveSuccessView(discord.ui.LayoutView):
    """View for blacklist remove success"""
    
    def __init__(self, server_id: str):
        super().__init__()
        
        content = (
            f"✅ **Server Unblacklisted**\n\n"
            f"Removed server `{server_id}` from blacklist.\n\n"
            f"The server can now use bot commands again."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class BlacklistRemoveNotFoundView(discord.ui.LayoutView):
    """View for server not blacklisted"""
    
    def __init__(self, server_id: str):
        super().__init__()
        
        content = (
            f"❌ **Not Blacklisted**\n\n"
            f"Server `{server_id}` is not blacklisted."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class BlacklistCheckFoundView(discord.ui.LayoutView):
    """View for when a server is blacklisted"""
    
    def __init__(self, server_id: str, server_name: str, entry):
        super().__init__()
        
        # Format the blacklisted date
        blacklisted_date = "Unknown"
        if entry.blacklisted_at:
            blacklisted_date = f"<t:{int(entry.blacklisted_at.timestamp())}:F>"
        
        content = (
            f"🚫 **Server is Blacklisted**\n\n"
            f"**Server Name:** {server_name}\n"
            f"**Server ID:** `{server_id}`\n"
            f"**Reason:** {entry.reason or 'No reason provided'}\n"
            f"**Blacklisted:** {blacklisted_date}\n\n"
            f"This server cannot use bot commands."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class BlacklistCheckNotFoundView(discord.ui.LayoutView):
    """View for when a server is not blacklisted"""
    
    def __init__(self, server_id: str):
        super().__init__()
        
        content = (
            f"✅ **Server is NOT Blacklisted**\n\n"
            f"Server `{server_id}` is not on the blacklist.\n"
            f"This server can use bot commands normally."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class NoBlacklistView(discord.ui.LayoutView):
    """View for empty blacklist"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "ℹ️ **No Blacklisted Servers**\n\n"
            "No servers are currently blacklisted."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.greyple().value
        )
        self.add_item(container)


class CacheReloadErrorView(discord.ui.LayoutView):
    """View for cache reload error"""
    
    def __init__(self, error: str):
        super().__init__()
        
        content = (
            f"❌ **Cache Reload Failed**\n\n"
            f"Error reloading cache:\n"
            f"`{error}`\n\n"
            f"_Please check the logs for more details_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ErrorNotFoundView(discord.ui.LayoutView):
    """View for error not found"""
    
    def __init__(self, error_id: str):
        super().__init__()
        
        content = (
            f"❌ **Error Not Found**\n\n"
            f"No error found with ID: `{error_id}`"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ErrorDeleteSuccessView(discord.ui.LayoutView):
    """View for error delete success"""
    
    def __init__(self, error_id: str):
        super().__init__()
        
        content = (
            f"✅ **Error Deleted**\n\n"
            f"Error `{error_id}` has been deleted from the database."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class ErrorDeleteFailedView(discord.ui.LayoutView):
    """View for error delete failed"""
    
    def __init__(self, error_id: str):
        super().__init__()
        
        content = (
            f"❌ **Delete Failed**\n\n"
            f"Could not delete error `{error_id}`.\n"
            f"It may not exist or has already been deleted."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class NoErrorsView(discord.ui.LayoutView):
    """View for no errors found"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "ℹ️ **No Errors Found**\n\n"
            "No errors found in the database.\n\n"
            "_Errors will appear here when they occur_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.greyple().value
        )
        self.add_item(container)


class ErrorsClearedView(discord.ui.LayoutView):
    """View for errors cleared"""
    
    def __init__(self, count: int):
        super().__init__()
        
        content = (
            f"✅ **Errors Cleared**\n\n"
            f"Cleared {count} error{'s' if count != 1 else ''} from the database.\n\n"
            f"_The error log is now empty_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class ErrorsClearFailedView(discord.ui.LayoutView):
    """View for errors clear failed"""
    
    def __init__(self, error_id: str):
        super().__init__()
        
        content = (
            f"❌ **Clear Failed**\n\n"
            f"Failed to clear errors from database.\n\n"
            f"Error ID: `{error_id}`\n\n"
            f"_Please check the logs for more details_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class OwnerOnlyView(discord.ui.LayoutView):
    """View for owner-only restriction message"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "❌ **Owner Only**\n\n"
            "This command is restricted to the bot owner.\n\n"
            "_If you need assistance, please contact the bot owner_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)