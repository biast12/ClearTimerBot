"""
View Display for Utility Commands
"""

import discord
from src.utils.footer import add_footer


class HelpView(discord.ui.LayoutView):
    """View for help command"""

    def __init__(self):
        super().__init__()

        bot_invite_url = (
            "https://discord.com/oauth2/authorize?"
            "client_id=1290353946308775987&permissions=277025483776&"
            "integration_type=0&scope=bot"
        )

        content = add_footer(
            "**ClearTimer Bot Help**\n\n"
            "Automatically clear messages in Discord channels on a schedule.\n\n"
            "**📝 Subscription Commands**\n"
            "`/subscription add <timer> [channel] [target]` - Subscribe channel with optional ignored target\n"
            "`/subscription remove [channel]` - Unsubscribe a channel\n"
            "`/subscription list` - List all active subscriptions\n"
            "`/subscription info [channel]` - View subscription details\n"
            "`/subscription update <timer> [channel] [target]` - Update timer with optional ignored target\n"
            "`/subscription ignore <target> [channel]` - Toggle message or user ignore status\n"
            "`/subscription clear [channel]` - Manually trigger a clear\n"
            "`/subscription skip [channel]` - Skip the next scheduled clear\n\n"
            "**🔧 Other Commands**\n"
            "`/ping` - Check bot latency\n"
            "`/help` - Show this help message\n\n"
            "**⏱️ Timer Formats**\n"
            "**Intervals:** `1d2h3m` (days, hours, minutes)\n"
            "**Daily Schedule:** `15:30 EST` (time + timezone)\n"
            "**Examples:** `24h`, `1d`, `30m`, `09:00 PST`\n\n"
            "**🔒 Required Permissions**\n"
            "**For You:** Manage Messages\n"
            "**For Bot:** View Channel, Send Messages, Send Messages in Threads, Read Message History, Manage Messages, Embed Links, Use Application Commands\n\n"
            "**🔗 Links**\n"
            f"[Support Server](https://biast12.com/support) | "
            f"[Add Bot]({bot_invite_url}) | "
            "[GitHub](https://github.com/biast12/ClearTimerBot)"
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class PingView(discord.ui.LayoutView):
    """View for ping command"""

    def __init__(self, ws_latency: int, response_time: int):
        super().__init__()

        # Determine status
        if ws_latency < 100:
            status = "🟢 Excellent"
        elif ws_latency < 200:
            status = "🟡 Good"
        elif ws_latency < 300:
            status = "🟠 Fair"
        else:
            status = "🔴 Poor"

        content = add_footer(
            f"🏓 **Pong!**\n\n"
            f"**WebSocket Latency:** {ws_latency}ms\n"
            f"**Response Time:** {response_time}ms\n"
            f"**Status:** {status}"
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class BlacklistedServerView(discord.ui.LayoutView):
    """View for blacklisted server error"""
    
    def __init__(self):
        super().__init__()
        
        content = add_footer(
            "❌ **Server Blacklisted**\n\n"
            "This server has been blacklisted and cannot use this bot.\n\n"
            "If you believe this is a mistake, you can appeal the blacklist on our [Support Server](https://biast12.com/support)."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)
