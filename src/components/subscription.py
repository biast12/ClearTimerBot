"""
View Display for Subscription Commands
"""

import discord
from typing import Optional, List, Tuple
from datetime import datetime
from src.utils.footer import add_footer


class SubscriptionSuccessView(discord.ui.LayoutView):
    """View for subscription success message"""
    
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
        
        content = add_footer(content)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class InvalidTimerView(discord.ui.LayoutView):
    """View for invalid timer error"""
    
    def __init__(self, error_message: str):
        super().__init__()
        
        content = add_footer(
            f"❌ **Invalid Timer**\n\n"
            f"{error_message}\n\n"
            f"**Valid Formats:**\n"
            f"• Intervals: `24h`, `1d12h`, `30m`\n"
            f"• Daily Schedule: `15:30 EST`, `09:00 PST`\n\n"
            f"_Use `/help` for more timer format examples_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class UnsubscribeSuccessView(discord.ui.LayoutView):
    """View for unsubscribe success"""
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        
        content = add_footer(
            f"✅ **Channel Unsubscribed**\n\n"
            f"{channel.mention} has been unsubscribed from automatic message deletion."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class NoActiveSubscriptionsView(discord.ui.LayoutView):
    """View for no active subscriptions error"""
    
    def __init__(self):
        super().__init__()
        
        content = add_footer(
            f"❌ **No Active Subscriptions**\n\n"
            f"No active subscriptions found in this server.\n\n"
            f"Use `/subscription add` to set up automatic clearing."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
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
        
        content += f"\n💡 Use `/subscription info` to view details for a specific channel"
        content = add_footer(content)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class ChannelNotSubscribedView(discord.ui.LayoutView):
    """View for channel not subscribed error"""
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        
        content = add_footer(
            f"❌ **Channel Not Subscribed**\n\n"
            f"{channel.mention} is not subscribed to message deletion.\n\n"
            f"Use `/subscription add` to set up automatic clearing first."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class SubscriptionInfoView(discord.ui.LayoutView):
    """View for comprehensive subscription information"""
    
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
        content = add_footer(content)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class UpdateSuccessView(discord.ui.LayoutView):
    """View for update success"""
    
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
        
        content = add_footer(content)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class InvalidTargetView(discord.ui.LayoutView):
    """View for invalid target format error"""
    
    def __init__(self):
        super().__init__()
        
        content = add_footer(
            f"❌ **Invalid Target Format**\n\n"
            f"Please provide a valid target:\n\n"
            f"**For messages:**\n"
            f"• Message ID: `123456789012345678`\n"
            f"• Message link: Discord message URL\n\n"
            f"**For users:**\n"
            f"• User mention: @username\n"
            f"• User ID: `123456789012345678`"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class NoSubscriptionDataView(discord.ui.LayoutView):
    """View for no subscription data error"""
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        
        content = add_footer(
            f"❌ **No Subscription Data**\n\n"
            f"Could not find subscription data for {channel.mention}.\n\n"
            f"The channel may not be subscribed or data may be corrupted.\n\n"
            f"_Try using `/subscription add` to re-subscribe the channel_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class UserNotFoundView(discord.ui.LayoutView):
    """View for user not found error"""
    
    def __init__(self, user_id: str):
        super().__init__()
        
        content = add_footer(
            f"❌ **User Not Found**\n\n"
            f"User with ID `{user_id}` not found in this server.\n\n"
            f"Please make sure the user is a member of this server."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class MessageNotFoundView(discord.ui.LayoutView):
    """View for message not found error"""
    
    def __init__(self, message_id: str, channel: discord.TextChannel):
        super().__init__()
        
        content = add_footer(
            f"❌ **Message Not Found**\n\n"
            f"Message with ID `{message_id}` not found in {channel.mention}.\n\n"
            f"Please make sure the message exists in the specified channel."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class IgnoreEntityView(discord.ui.LayoutView):
    """View for ignore entity (message or user) add/remove"""
    
    def __init__(self, entity_type: str, entity_id: str, channel: discord.TextChannel, added: bool):
        super().__init__()
        
        entity_name = entity_type.lower()
        
        if added:
            content = add_footer(
                f"✅ **{entity_type} Added to Ignore List**\n\n"
                f"{entity_type} `{entity_id}` will be ignored during clearing in {channel.mention}."
            )
        else:
            content = add_footer(
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


class ManualClearSuccessView(discord.ui.LayoutView):
    """View for manual clear success"""
    
    def __init__(self, deleted_count: int, channel: discord.TextChannel):
        super().__init__()
        
        content = add_footer(
            f"✅ **Messages Cleared**\n\n"
            f"Manually cleared {deleted_count} message{'s' if deleted_count != 1 else ''} from {channel.mention}."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class JobNotFoundView(discord.ui.LayoutView):
    """View for scheduled job not found error"""
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        
        content = add_footer(
            f"❌ **Scheduled Job Not Found**\n\n"
            f"Could not find the scheduled job for {channel.mention}.\n\n"
            f"The channel may not be subscribed or the scheduler may need to be refreshed.\n\n"
            f"_Try using `/subscription info` to check the subscription status_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class SkipSuccessView(discord.ui.LayoutView):
    """View for skip success"""
    
    def __init__(self, channel: discord.TextChannel, next_run_time: datetime):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = add_footer(
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


class NextTimeNotFoundView(discord.ui.LayoutView):
    """View for next scheduled time not found error"""
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        
        content = add_footer(
            f"❌ **Schedule Error**\n\n"
            f"Could not determine the next scheduled time for {channel.mention}.\n\n"
            f"This may be a temporary issue with the scheduler.\n\n"
            f"_Try again in a few moments or contact support if the issue persists_"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class MultipleIgnoreEntityView(discord.ui.LayoutView):
    """View for multiple ignore entity operations"""
    
    def __init__(
        self,
        channel: discord.TextChannel,
        added_users: List[str],
        removed_users: List[str],
        added_messages: List[str],
        removed_messages: List[str]
    ):
        super().__init__()
        
        content_parts = []
        
        # Build content based on what was added/removed
        if added_users:
            user_mentions = [f"<@{uid}>" for uid in added_users]
            content_parts.append(f"✅ **Added Users to Ignore List:** {', '.join(user_mentions)}")
        
        if removed_users:
            user_mentions = [f"<@{uid}>" for uid in removed_users]
            content_parts.append(f"❌ **Removed Users from Ignore List:** {', '.join(user_mentions)}")
        
        if added_messages:
            content_parts.append(f"✅ **Added Messages to Ignore List:** {len(added_messages)} message(s)")
            content_parts.append(f"   IDs: {', '.join(added_messages)}")
        
        if removed_messages:
            content_parts.append(f"❌ **Removed Messages from Ignore List:** {len(removed_messages)} message(s)")
            content_parts.append(f"   IDs: {', '.join(removed_messages)}")
        
        if not content_parts:
            content_parts.append("ℹ️ **No changes made** - All targets were already in their respective states")
        
        content = f"**Ignore List Updated for {channel.mention}**\n\n" + "\n\n".join(content_parts)
        content = add_footer(content)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value if (added_users or added_messages) else discord.Color.orange().value
        )
        self.add_item(container)


class SubscriptionSuccessWithMultipleIgnoresView(discord.ui.LayoutView):
    """View for subscription success with multiple ignored targets"""
    
    def __init__(
        self,
        channel: discord.TextChannel,
        timer: str,
        next_run_time: datetime,
        added_targets: List[Tuple[str, str]]
    ):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"✅ **Channel Subscribed**\n\n"
            f"Messages in {channel.mention} will be cleared automatically.\n\n"
            f"**Timer:** {timer}\n"
            f"**Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        if added_targets:
            users = [f"<@{entity_id}>" for entity_id, entity_type in added_targets if entity_type == "user"]
            messages = [entity_id for entity_id, entity_type in added_targets if entity_type == "message"]
            
            if users:
                content += f"\n\n**Ignored Users:** {', '.join(users)}"
            if messages:
                content += f"\n**Ignored Messages:** {len(messages)} message(s) - IDs: {', '.join(messages)}"
        
        content = add_footer(content)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class UpdateSuccessWithMultipleIgnoresView(discord.ui.LayoutView):
    """View for update success with multiple ignored targets"""
    
    def __init__(
        self,
        channel: discord.TextChannel,
        timer: str,
        next_run_time: datetime,
        added_targets: List[Tuple[str, str]]
    ):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"✅ **Subscription Updated**\n\n"
            f"Timer for {channel.mention} has been updated.\n\n"
            f"**New Timer:** {timer}\n"
            f"**Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        if added_targets:
            users = [f"<@{entity_id}>" for entity_id, entity_type in added_targets if entity_type == "user"]
            messages = [entity_id for entity_id, entity_type in added_targets if entity_type == "message"]
            
            content += "\n\n**Newly Added to Ignore List:**"
            if users:
                content += f"\n• **Users:** {', '.join(users)}"
            if messages:
                content += f"\n• **Messages:** {len(messages)} message(s) - IDs: {', '.join(messages)}"
        
        content = add_footer(content)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)