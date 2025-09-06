"""
View Display for Owner Commands
"""

import discord
import os


class OwnerOnlyView(discord.ui.LayoutView):
    """View for owner-only restriction message"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "🔒 **Owner Only**\n\n"
            "This command is restricted to the bot owner."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class NoAdminsView(discord.ui.LayoutView):
    """View for no admins found"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "📋 **No Admins Configured**\n\n"
            "There are no administrators configured.\n\n"
            "_Use `/owner admin add` to add administrators_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.greyple().value
        )
        self.add_item(container)


class AdminListView(discord.ui.LayoutView):
    """View for listing all admins"""
    
    def __init__(self, admins: set, bot):
        super().__init__()
        
        content = "👥 **Bot Administrators**\n\n"
        
        for user_id in sorted(admins):
            # Try to get current username from bot
            try:
                user = bot.get_user(int(user_id))
                current_name = str(user) if user else f"User {user_id}"
            except:
                current_name = f"User {user_id}"
            
            content += f"• **{current_name}**\n"
            content += f"  ID: `{user_id}`\n"
            content += f"  Mention: <@{user_id}>\n\n"
        
        admin_count = len(admins)
        admin_text = "administrator" if admin_count == 1 else "administrators"
        content += f"_Total: {admin_count} {admin_text}_"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class AdminAddSuccessView(discord.ui.LayoutView):
    """View for successful admin addition"""
    
    def __init__(self, username: str, user_id: str):
        super().__init__()
        
        content = (
            "✅ **Administrator Added**\n\n"
            f"Successfully added **{username}** as a bot administrator.\n\n"
            f"**User ID:** `{user_id}`\n"
            f"**Mention:** <@{user_id}>\n\n"
            "_This user can now use admin commands_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class AdminAddAlreadyView(discord.ui.LayoutView):
    """View for admin already exists"""
    
    def __init__(self, user_id: str):
        super().__init__()
        
        content = (
            "⚠️ **Already Administrator**\n\n"
            f"User `{user_id}` is already a bot administrator.\n"
            f"Mention: <@{user_id}>"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)


class AdminAddSelfView(discord.ui.LayoutView):
    """View for trying to add yourself as admin when you're the owner"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "⚠️ **Already Owner**\n\n"
            "You are the bot owner and already have full permissions.\n\n"
            "_No need to add yourself as an administrator_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)


class AdminRemoveSuccessView(discord.ui.LayoutView):
    """View for successful admin removal"""
    
    def __init__(self, user_id: str):
        super().__init__()
        
        content = (
            "✅ **Administrator Removed**\n\n"
            f"Successfully removed `{user_id}` from administrators.\n"
            f"Previous admin: <@{user_id}>\n\n"
            "_This user can no longer use admin commands_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class AdminRemoveNotFoundView(discord.ui.LayoutView):
    """View for admin not found"""
    
    def __init__(self, user_id: str):
        super().__init__()
        
        content = (
            "❌ **Not an Administrator**\n\n"
            f"User `{user_id}` is not a bot administrator.\n\n"
            "_Cannot remove someone who isn't an admin_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)






class ShardReloadSingleView(discord.ui.LayoutView):
    """View for reloading a single shard"""
    
    def __init__(self, shard_id: int):
        super().__init__()
        
        content = (
            "🔄 **Reloading Single Shard**\n\n"
            f"Restarting shard {shard_id} only...\n\n"
            "**What happens:**\n"
            "• Only this specific shard restarts\n"
            "• Other shards continue running\n"
            "• Guilds on this shard temporarily offline"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)




class ShardNotShardedView(discord.ui.LayoutView):
    """View for when bot is not sharded but shard reload is requested"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "⚠️ **Cannot Reload Shard**\n\n"
            "Bot is running in single-instance mode (not sharded).\n\n"
            "_Use `/owner shard reload` to reload the bot_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ShardInvalidIdView(discord.ui.LayoutView):
    """View for invalid shard ID"""
    
    def __init__(self, shard_id: int, max_shard: int):
        super().__init__()
        
        content = (
            "❌ **Invalid Shard ID**\n\n"
            f"Shard ID `{shard_id}` is invalid.\n\n"
            f"**Valid Range:** 0 to {max_shard - 1}\n\n"
            "_Please specify a valid shard ID_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ShardReloadSignalView(discord.ui.LayoutView):
    """View for reload signal sent to another shard"""
    
    def __init__(self, shard_id: int):
        super().__init__()
        
        content = (
            "📡 **Reload Signal Sent**\n\n"
            f"Reload signal sent to shard {shard_id}.\n\n"
            "**Note:** Cross-shard communication is not yet implemented.\n"
            "Please restart the shard manually.\n\n"
            "_Future updates will enable automatic cross-shard reloading_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class ShardReloadFailedView(discord.ui.LayoutView):
    """View for shard reload failure"""
    
    def __init__(self, error: str):
        super().__init__()
        
        content = (
            "❌ **Reload Failed**\n\n"
            "Failed to reload shard.\n\n"
            f"**Error:** {error}\n\n"
            "_Please check the logs for more details_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)




class ShardStatusCompleteView(discord.ui.LayoutView):
    """View for shard status"""
    
    def __init__(self, bot):
        super().__init__()
        
        content = "🔷 **Shard Status**\n\n"
        
        # Current runtime status
        content += "**Current Runtime:**\n"
        if bot.shard_id is not None:
            content += f"• Shard: {bot.shard_id}/{bot.shard_count - 1}\n"
            content += f"• Total Shards: {bot.shard_count}\n"
            content += f"• Guilds on This Shard: {len(bot.guilds)}\n"
            
            # Get shard latency
            latency = bot.get_shard(bot.shard_id).latency if bot.get_shard(bot.shard_id) else bot.latency
            content += f"• Latency: {latency * 1000:.2f}ms\n"
        else:
            content += "• Mode: Single-instance (not sharded)\n"
            content += f"• Total Guilds: {len(bot.guilds)}\n"
            content += f"• Latency: {bot.latency * 1000:.2f}ms\n"
        
        content += f"• Process ID: `{os.getpid()}`\n\n"
        
        content += "**Available Commands:**\n"
        content += "• `/owner shard reload` - Reload all shards\n"
        content += "• `/owner shard reload <id>` - Reload specific shard\n"
        content += "• `/owner shard status` - View this status"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)




class ShardRestartView(discord.ui.LayoutView):
    """View for restarting all shards"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "🔄 **Reloading All Shards**\n\n"
            "Full bot reload initiated...\n\n"
            "**What happens:**\n"
            "• All shards shut down together\n"
            "• Shard manager restarts\n"
            "• All shards relaunch with fresh state\n"
            "• Bot offline for ~5-10 seconds\n\n"
            "_Use `/owner shard reload <id>` to reload single shard only_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)