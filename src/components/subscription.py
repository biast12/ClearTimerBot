"""
Discord Components v2 for Subscription Commands
"""

import discord
from typing import Optional
from datetime import datetime


class SubscriptionSuccessView(discord.ui.LayoutView):
    """View for subscription success message using Components v2"""
    
    def __init__(self, channel: discord.TextChannel, timer: str, next_run_time: datetime, 
                 ignored_entity_id: Optional[str] = None, ignored_entity_type: Optional[str] = None):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"✅ **Channel Subscribed**\n\n"
            f"Messages in {channel.mention} will be cleared automatically.\n\n"
            f"**Timer:** {timer}\n"
            f"**Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        if ignored_entity_id and ignored_entity_type:
            if ignored_entity_type == "user":
                content += f"\n\n**Ignored User:** <@{ignored_entity_id}>"
            else:
                content += f"\n\n**Ignored Message:** Message ID: {ignored_entity_id}"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class IgnoreEntityView(discord.ui.LayoutView):
    """View for ignore entity (message or user) add/remove using Components v2"""
    
    def __init__(self, entity_type: str, entity_id: str, channel: discord.TextChannel, added: bool):
        super().__init__()
        
        entity_name = entity_type.lower()
        
        if added:
            content = (
                f"✅ **{entity_type} Added to Ignore List**\n\n"
                f"{entity_type} `{entity_id}` will be ignored during clearing in {channel.mention}."
            )
        else:
            content = (
                f"✅ **{entity_type} Removed from Ignore List**\n\n"
                f"{entity_type} `{entity_id}` will no longer be ignored in {channel.mention}."
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


# Keep backward compatibility
class IgnoreMessageView(IgnoreEntityView):
    """Backward compatibility for ignore message view"""
    
    def __init__(self, title: str, message_id: str, channel: discord.TextChannel, added: bool):
        super().__init__("Message", message_id, channel, added)


class SubscriptionInfoView(discord.ui.LayoutView):
    """View for comprehensive subscription information using Components v2"""
    
    def __init__(self, channel: discord.TextChannel, next_run_time: datetime, timer_info=None):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"📊 **Subscription Information**\n\n"
            f"**Channel:** {channel.mention}\n"
            f"**Status:** ✅ Active\n\n"
        )
        
        if timer_info:
            content += f"**Timer Configuration:** {timer_info.timer}\n"
            
            # Show ignored messages if any
            if hasattr(timer_info, 'ignored') and timer_info.ignored.messages:
                content += f"**Ignored Messages:** {len(timer_info.ignored.messages)} message(s)\n"
                # List first 5 message IDs with clickable links
                for i, msg_id in enumerate(list(timer_info.ignored.messages)[:5]):
                    # Create message link - need to get guild_id from channel
                    msg_link = f"https://discord.com/channels/{channel.guild.id}/{channel.id}/{msg_id}"
                    content += f"  • [`{msg_id}`]({msg_link})\n"
                if len(timer_info.ignored.messages) > 5:
                    content += f"  • ... and {len(timer_info.ignored.messages) - 5} more\n"
            else:
                content += "**Ignored Messages:** None\n"
            
            # Show ignored users if any
            if hasattr(timer_info, 'ignored') and timer_info.ignored.users:
                content += f"**Ignored Users:** {len(timer_info.ignored.users)} user(s)\n"
                # List first 5 user mentions
                for i, user_id in enumerate(list(timer_info.ignored.users)[:5]):
                    content += f"  • <@{user_id}> (ID: `{user_id}`)\n"
                if len(timer_info.ignored.users) > 5:
                    content += f"  • ... and {len(timer_info.ignored.users) - 5} more\n"
            else:
                content += "**Ignored Users:** None\n"
        
        content += (
            f"\n**Schedule Details**\n"
            f"**Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class SubscriptionListView(discord.ui.LayoutView):
    """View for listing all active subscriptions in a server"""
    
    def __init__(self, guild: discord.Guild, channels: dict, scheduler_service):
        super().__init__()
        
        content = f"📋 **Active Subscriptions for {guild.name}**\n\n"
        
        if not channels:
            content += "No active subscriptions found."
        else:
            for channel_id, timer_info in channels.items():
                channel = guild.get_channel(int(channel_id))
                if channel:
                    # Get next run time from scheduler
                    next_run_time = scheduler_service.get_channel_next_clear_time(str(guild.id), channel_id)
                    
                    content += f"**#{channel.name}**\n"
                    content += f"  • Timer: {timer_info.timer}\n"
                    
                    if next_run_time:
                        timestamp = int(next_run_time.timestamp())
                        content += f"  • Next clear: <t:{timestamp}:R>\n"
                    
                    # Show ignored entities
                    if hasattr(timer_info, 'ignored'):
                        ignored_msgs = []
                        ignored_users = []
                        
                        if timer_info.ignored.messages:
                            for msg_id in timer_info.ignored.messages:
                                # Create message link
                                msg_link = f"https://discord.com/channels/{guild.id}/{channel_id}/{msg_id}"
                                ignored_msgs.append(f"[Message]({msg_link})")
                        
                        if timer_info.ignored.users:
                            for user_id in timer_info.ignored.users:
                                ignored_users.append(f"<@{user_id}>")
                        
                        if ignored_msgs or ignored_users:
                            content += f"  • Ignored: "
                            parts = []
                            if ignored_msgs:
                                parts.append(f"{len(ignored_msgs)} message{'s' if len(ignored_msgs) > 1 else ''}: {', '.join(ignored_msgs[:3])}" + 
                                           (f" (+{len(ignored_msgs)-3} more)" if len(ignored_msgs) > 3 else ""))
                            if ignored_users:
                                parts.append(f"{len(ignored_users)} user{'s' if len(ignored_users) > 1 else ''}: {', '.join(ignored_users[:3])}" + 
                                           (f" (+{len(ignored_users)-3} more)" if len(ignored_users) > 3 else ""))
                            content += " | ".join(parts) + "\n"
                    
                    content += "\n"
        
        content += f"\n💡 Use `/sub info` to view details for a specific channel"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class SkipSuccessView(discord.ui.LayoutView):
    """View for skip success using Components v2"""
    
    def __init__(self, channel: discord.TextChannel, next_run_time: datetime):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"⏭️ **Next Clear Skipped**\n\n"
            f"Skipped the next scheduled clear for {channel.mention}.\n\n"
            f"**New Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.orange().value
        )
        self.add_item(container)


class UpdateSuccessView(discord.ui.LayoutView):
    """View for update success using Components v2"""
    
    def __init__(self, channel: discord.TextChannel, timer: str, next_run_time: datetime, 
                 ignored_entity_id: Optional[str] = None, ignored_entity_type: Optional[str] = None):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"🔄 **Subscription Updated**\n\n"
            f"Successfully updated the timer for {channel.mention}.\n\n"
            f"**New Timer:** {timer}\n"
            f"**Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        if ignored_entity_id and ignored_entity_type:
            if ignored_entity_type == "user":
                content += f"\n\n**Added Ignored User:** <@{ignored_entity_id}>"
            else:
                content += f"\n\n**Added Ignored Message:** Message ID: {ignored_entity_id}"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
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
            accent_color=discord.Color.green().value
        )
        self.add_item(container)