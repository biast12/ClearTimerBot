"""
Discord Components v2 for Information Commands
"""

import discord
from datetime import datetime


class NextClearView(discord.ui.LayoutView):
    """View for next clear information using Components v2"""
    
    def __init__(self, channel: discord.TextChannel, next_run_time: datetime, timer_info=None):
        super().__init__()
        
        timestamp = int(next_run_time.timestamp())
        
        content = (
            f"⏰ **Next Clear Scheduled**\n\n"
            f"Message clear information for {channel.mention}\n\n"
        )
        
        if timer_info:
            content += f"**Timer:** {timer_info.timer}\n"
        
        content += (
            f"**Next Clear:** <t:{timestamp}:f>\n"
            f"**Time Until:** <t:{timestamp}:R>"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value  # Blue for info
        )
        self.add_item(container)


class HelpView(discord.ui.LayoutView):
    """View for help command using Components v2"""
    
    def __init__(self):
        super().__init__()
        
        bot_invite_url = (
            "https://discord.com/oauth2/authorize?"
            "client_id=1290353946308775987&permissions=277025483776&"
            "integration_type=0&scope=bot"
        )
        
        content = (
            "**ClearTimer Bot Help**\n\n"
            "Automatically clear messages in Discord channels on a schedule.\n\n"
            "**📝 Basic Commands**\n"
            "`/sub <timer> [channel]` - Subscribe a channel to automatic clearing\n"
            "`/unsub [channel]` - Unsubscribe a channel\n"
            "`/next [channel]` - Check next clear time\n"
            "`/ping` - Check bot latency\n"
            "`/help` - Show this help message\n\n"
            "**⏱️ Timer Formats**\n"
            "**Intervals:** `1d2h3m` (days, hours, minutes)\n"
            "**Daily Schedule:** `15:30 EST` (time + timezone)\n"
            "**Examples:** `24h`, `1d`, `30m`, `09:00 PST`\n\n"
            "**🔒 Required Permissions**\n"
            "**For You:** Manage Messages\n"
            "**For Bot:** Read Messages, Manage Messages, Read Message History\n\n"
            "**🔗 Links**\n"
            f"[Support Server](https://discord.com/invite/ERFffj9Qs7) | "
            f"[Add Bot]({bot_invite_url}) | "
            "[GitHub](https://github.com/biast12/ClearTimerBot)"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value  # Blue for info
        )
        self.add_item(container)