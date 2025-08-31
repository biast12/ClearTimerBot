"""
Discord Components v2 for Subscription Commands
"""

import discord
from typing import Optional
from datetime import datetime


class SubscriptionSuccessView(discord.ui.LayoutView):
    """View for subscription success message using Components v2"""
    
    def __init__(self, channel: discord.TextChannel, timer: str, next_run_time: datetime, message_id: Optional[str] = None):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"✅ **Channel Subscribed**\n\n"
            f"Messages in {channel.mention} will be cleared automatically.\n\n"
            f"**Timer:** {timer}\n"
            f"**Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        if message_id:
            content += f"\n\n**Ignored Message:** Message ID: {message_id}"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value  # Green for success
        )
        self.add_item(container)


class IgnoreMessageView(discord.ui.LayoutView):
    """View for ignore message add/remove using Components v2"""
    
    def __init__(self, title: str, message_id: str, channel: discord.TextChannel, added: bool):
        super().__init__()
        
        if added:
            content = (
                f"✅ **Message Added to Ignore List**\n\n"
                f"Message `{message_id}` will be ignored during clearing in {channel.mention}."
            )
        else:
            content = (
                f"✅ **Message Removed from Ignore List**\n\n"
                f"Message `{message_id}` will no longer be ignored in {channel.mention}."
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value  # Green for success
        )
        self.add_item(container)


class UnsubscribeSuccessView(discord.ui.LayoutView):
    """View for unsubscribe success using Components v2"""
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        
        content = (
            f"✅ **Channel Unsubscribed**\n\n"
            f"{channel.mention} has been unsubscribed from automatic message deletion."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value  # Green for success
        )
        self.add_item(container)