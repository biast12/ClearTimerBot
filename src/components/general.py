"""
View Display for General Commands
"""

import discord
from discord import app_commands
from typing import Dict
from src.utils.footer import add_footer
from src.config import get_global_config


class HelpView(discord.ui.LayoutView):
    """View for help command with dynamic command listing"""

    def __init__(self, translator, commands_dict):
        super().__init__()
        self.translator = translator
        self.commands_dict = commands_dict
        
        # Create the main help display
        self.create_help_display()
        
        # Don't add dropdown for now - incompatible with LayoutView

    def create_help_display(self):
        config = get_global_config()
        
        sections = []
        
        sections.append(f"**{config.bot_name} {self.translator.get('commands.help.title')}**\n")
        sections.append(self.translator.get("commands.help.description") + "\n")
        
        all_commands = self.commands_dict or {'subscription': [], 'general': []}
        
        if all_commands.get('subscription'):
            sections.append(f"**{self.translator.get('commands.help.subscription_commands')}**")
            for cmd in all_commands['subscription']:
                sections.append(f"`/{cmd['name']}` - {cmd['description']}")
            sections.append("")
        
        if all_commands.get('general'):
            sections.append(f"**{self.translator.get('commands.help.other_commands')}**")
            for cmd in all_commands['general']:
                sections.append(f"`/{cmd['name']}` - {cmd['description']}")
            sections.append("")
        
        sections.append(f"**{self.translator.get('commands.help.timer_formats')}**")
        sections.append(self.translator.get("commands.help.timer_intervals"))
        sections.append(self.translator.get("commands.help.timer_daily"))
        sections.append(self.translator.get("commands.help.timer_examples") + "\n")
        
        sections.append(f"**{self.translator.get('commands.help.required_permissions')}**")
        sections.append(self.translator.get("commands.help.permissions_for_you"))
        sections.append(self.translator.get("commands.help.permissions_for_bot") + "\n")
        
        sections.append(f"**{self.translator.get('commands.help.links')}**")
        sections.append(
            f"[Support Server]({config.support_server_url}) | "
            f"[Add Bot]({config.bot_invite_url}) | "
            f"[GitHub]({config.github_url})"
        )
        
        content = add_footer("\n".join(sections), self.translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)
    


class PingView(discord.ui.LayoutView):
    """View for ping command"""

    def __init__(self, ws_latency: int, response_time: int, translator):
        super().__init__()

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
        
        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class BlacklistedServerView(discord.ui.LayoutView):
    """View for blacklisted server error"""
    
    def __init__(self, translator):
        super().__init__()
        
        content = add_footer(translator.get("validation.blacklisted_server"), translator)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class LanguageListView(discord.ui.LayoutView):
    """View for displaying available languages"""
    
    def __init__(self, languages: Dict[str, str], current_language: str, translator):
        super().__init__()
        
        language_lines = []
        language_lines.append(f"**{translator.get('commands.language.list.title')}**\n")
        language_lines.append(translator.get("commands.language.list.description") + "\n")
        
        current_name = languages.get(current_language, current_language)
        language_lines.append(translator.get("commands.language.list.current", language=current_name) + "\n")
        
        for code, name in sorted(languages.items()):
            language_lines.append(f"• {name} (`{code}`)")
        
        language_lines.append("")
        language_lines.append(translator.get("commands.language.list.change_hint"))
        
        content = add_footer("\n".join(language_lines), translator)
        
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
        content = add_footer(message, translator)
        
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
        content = add_footer(message, translator)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class LanguageInvalidView(discord.ui.LayoutView):
    """View for when an invalid language code is provided"""
    
    def __init__(self, invalid_language: str, available_languages: list, translator):
        super().__init__()
        
        languages_str = ", ".join([f"`{lang}`" for lang in sorted(available_languages)])
        
        message = translator.get("commands.language.change.invalid", language=invalid_language)
        available_msg = translator.get("commands.language.change.available", languages=languages_str)
        
        full_message = f"{message}\n{available_msg}"
        content = add_footer(full_message, translator)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


