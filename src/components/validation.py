"""
View Display for Validation Errors
"""

import discord
from typing import Optional
from src.utils.footer import add_footer


class ValidationErrorView(discord.ui.LayoutView):
    """View for validation error messages"""
    
    def __init__(self, error_message: str):
        super().__init__()
        
        # Parse the error message to determine type and format
        if "blacklisted" in error_message.lower():
            title = "Server Blacklisted"
            color = discord.Color.red()
        elif "permission" in error_message.lower() and "You need" in error_message:
            title = "Insufficient Permissions"
            color = discord.Color.orange()
        elif "missing the following permissions" in error_message:
            title = "Bot Missing Permissions"
            color = discord.Color.orange()
        elif "not subscribed" in error_message:
            title = "Channel Not Subscribed"
            color = discord.Color.yellow()
        elif "already has a timer" in error_message:
            title = "Channel Already Subscribed"
            color = discord.Color.yellow()
        else:
            title = "Validation Error"
            color = discord.Color.red()
        
        # Clean up the message for better formatting
        clean_message = error_message.replace("❌ ", "")
        
        content = add_footer(f"❌ **{title}**\n\n{clean_message}")
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=color.value
        )
        self.add_item(container)


class BlacklistErrorView(discord.ui.LayoutView):
    """Specialized view for blacklist errors"""
    
    def __init__(self):
        super().__init__()
        
        content = add_footer(
            "❌ **Server Blacklisted**\n\n"
            "This server has been blacklisted and cannot use this bot.\n\n"
            "If you believe this is a mistake, please contact support."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class PermissionErrorView(discord.ui.LayoutView):
    """Specialized view for permission errors"""
    
    def __init__(self, missing_permissions: str, channel: Optional[discord.TextChannel] = None):
        super().__init__()
        
        if channel:
            content = add_footer(
                f"❌ **Bot Missing Permissions**\n\n"
                f"I'm missing the following permissions in {channel.mention}:\n"
                f"{missing_permissions}\n\n"
                f"Please grant these permissions and try again."
            )
        else:
            content = add_footer(
                f"❌ **Insufficient Permissions**\n\n"
                f"You need the following permission to use this command:\n"
                f"{missing_permissions}\n\n"
                f"Please contact a server administrator if you need access."
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.orange().value
        )
        self.add_item(container)


class SubscriptionStatusErrorView(discord.ui.LayoutView):
    """Specialized view for subscription status errors"""
    
    def __init__(self, channel: discord.TextChannel, is_subscribed: bool):
        super().__init__()
        
        if is_subscribed:
            content = add_footer(
                f"❌ **Channel Already Subscribed**\n\n"
                f"{channel.mention} already has a timer set.\n\n"
                f"Use `/subscription update` to update the subscription instead."
            )
        else:
            content = add_footer(
                f"❌ **Channel Not Subscribed**\n\n"
                f"{channel.mention} is not subscribed to message deletion.\n\n"
                f"Use `/subscription add` to set up automatic clearing first."
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)