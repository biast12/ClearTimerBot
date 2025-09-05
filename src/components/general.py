"""
View Display for General Commands
"""

import discord
from typing import Dict
from src.utils.footer import add_footer
from src.config import get_global_config


class HelpView(discord.ui.LayoutView):
    """View for help command"""

    def __init__(self, translator):
        super().__init__()

        config = get_global_config()
        
        # Build the help text using translations
        sections = []
        
        # Title and description
        sections.append(f"**{config.bot_name} {translator.get('commands.help.title')}**\n")
        sections.append(translator.get("commands.help.description") + "\n")
        
        # Subscription commands
        sections.append(f"**{translator.get('commands.help.subscription_commands')}**")
        sections.append("`/subscription add <timer> [channel] [target]` - Subscribe channel")
        sections.append("`/subscription remove [channel]` - Unsubscribe a channel")
        sections.append("`/subscription list` - List all active subscriptions")
        sections.append("`/subscription info [channel]` - View subscription details")
        sections.append("`/subscription update <timer> [channel] [target]` - Update timer")
        sections.append("`/subscription ignore <target> [channel]` - Toggle message or user ignore status")
        sections.append("`/subscription clear [channel]` - Manually trigger a clear")
        sections.append("`/subscription skip [channel]` - Skip the next scheduled clear\n")
        
        # Other commands
        sections.append(f"**{translator.get('commands.help.other_commands')}**")
        sections.append("`/ping` - Check bot latency")
        sections.append("`/help` - Show this help message")
        sections.append("`/timezone list` - List available timezones")
        sections.append("`/timezone change <timezone>` - Change server timezone")
        sections.append("`/language list` - Show available languages")
        sections.append("`/language change <language>` - Change server language\n")
        
        # Timer formats
        sections.append(f"**{translator.get('commands.help.timer_formats')}**")
        sections.append(translator.get("commands.help.timer_intervals"))
        sections.append(translator.get("commands.help.timer_daily"))
        sections.append(translator.get("commands.help.timer_examples") + "\n")
        
        # Required permissions
        sections.append(f"**{translator.get('commands.help.required_permissions')}**")
        sections.append(translator.get("commands.help.permissions_for_you"))
        sections.append(translator.get("commands.help.permissions_for_bot") + "\n")
        
        # Links
        sections.append(f"**{translator.get('commands.help.links')}**")
        sections.append(
            f"[Support Server]({config.support_server_url}) | "
            f"[Add Bot]({config.bot_invite_url}) | "
            f"[GitHub]({config.github_url})"
        )
        
        content = add_footer("\n".join(sections))

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class PingView(discord.ui.LayoutView):
    """View for ping command"""

    def __init__(self, ws_latency: int, response_time: int, translator):
        super().__init__()

        # Determine status
        if ws_latency < 100:
            status_key = "commands.ping.status_excellent"
        elif ws_latency < 200:
            status_key = "commands.ping.status_good"
        elif ws_latency < 300:
            status_key = "commands.ping.status_fair"
        else:
            status_key = "commands.ping.status_poor"

        lines = [
            translator.get("commands.ping.title"),
            "",
            translator.get("commands.ping.websocket_latency", latency=ws_latency),
            translator.get("commands.ping.response_time", time=response_time),
            translator.get("commands.ping.status", status=translator.get(status_key))
        ]
        
        content = add_footer("\n".join(lines))

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class BlacklistedServerView(discord.ui.LayoutView):
    """View for blacklisted server error"""
    
    def __init__(self, translator):
        super().__init__()
        
        content = add_footer(translator.get("common.blacklisted_server"))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class LanguageListView(discord.ui.LayoutView):
    """View for displaying available languages"""
    
    def __init__(self, languages: Dict[str, str], current_language: str, translator):
        super().__init__()
        
        # Build language list
        language_lines = []
        language_lines.append(f"**{translator.get('commands.language.list.title')}**\n")
        language_lines.append(translator.get("commands.language.list.description") + "\n")
        
        # Current language
        current_name = languages.get(current_language, current_language)
        language_lines.append(translator.get("commands.language.list.current", language=current_name) + "\n")
        
        # Available languages
        for code, name in sorted(languages.items()):
            if code == current_language:
                language_lines.append(f"• **{name}** (`{code}`) ✓")
            else:
                language_lines.append(f"• {name} (`{code}`)")
        
        language_lines.append("")
        language_lines.append(translator.get("commands.language.list.change_hint"))
        
        content = add_footer("\n".join(language_lines))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class LanguageChangeSuccessView(discord.ui.LayoutView):
    """View for successful language change"""
    
    def __init__(self, language_name: str, translator):
        super().__init__()
        
        message = translator.get("commands.language.change.success", language=language_name)
        content = add_footer(message)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class LanguageAlreadySetView(discord.ui.LayoutView):
    """View for when language is already set"""
    
    def __init__(self, language_name: str, translator):
        super().__init__()
        
        message = translator.get("commands.language.change.already_set", language=language_name)
        content = add_footer(message)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class InvalidLanguageView(discord.ui.LayoutView):
    """View for invalid language selection"""
    
    def __init__(self, language: str, available_languages: Dict[str, str], translator):
        super().__init__()
        
        lines = []
        lines.append(translator.get("commands.language.change.invalid", language=language))
        lines.append("")
        
        # List available languages
        lines.append(translator.get("commands.language.change.available", 
                                   languages=", ".join([f"{name} (`{code}`)" for code, name in available_languages.items()])))
        
        content = add_footer("\n".join(lines))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)