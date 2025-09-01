"""
View Display for Owner Commands
"""

import discord
from discord.ext import commands


class OwnerOnlyView(discord.ui.LayoutView):
    """View for owner-only restriction message"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "🔒 **Owner Only**\n\n"
            "This command is restricted to the bot owner.\n\n"
            "_Only the original bot owner can use this command_"
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



class ConfigReloadSuccessView(discord.ui.LayoutView):
    """View for successful config reload"""
    
    def __init__(self, admin_count: int):
        super().__init__()
        
        content = (
            "✅ **Configuration Reloaded**\n\n"
            f"Successfully reloaded bot configuration from database.\n\n"
            f"**Active Administrators:** {admin_count}"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class ConfigReloadErrorView(discord.ui.LayoutView):
    """View for config reload error"""
    
    def __init__(self, error: str):
        super().__init__()
        
        content = (
            "❌ **Configuration Reload Failed**\n\n"
            f"Failed to reload configuration from database.\n\n"
            f"**Error:** {error}"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)