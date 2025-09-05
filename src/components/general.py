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
        
        # Build the help text using translations
        sections = []
        
        # Title and description
        sections.append(f"**{config.bot_name} {self.translator.get('commands.help.title')}**\n")
        sections.append(self.translator.get("commands.help.description") + "\n")
        
        # Use the dynamically provided commands
        all_commands = self.commands_dict or {'subscription': [], 'general': []}
        
        # Subscription commands
        if all_commands.get('subscription'):
            sections.append(f"**{self.translator.get('commands.help.subscription_commands')}**")
            for cmd in all_commands['subscription']:
                sections.append(f"`/{cmd['name']}` - {cmd['description']}")
            sections.append("")
        
        # General commands
        if all_commands.get('general'):
            sections.append(f"**{self.translator.get('commands.help.other_commands')}**")
            for cmd in all_commands['general']:
                sections.append(f"`/{cmd['name']}` - {cmd['description']}")
            sections.append("")
        
        # Timer formats
        sections.append(f"**{self.translator.get('commands.help.timer_formats')}**")
        sections.append(self.translator.get("commands.help.timer_intervals"))
        sections.append(self.translator.get("commands.help.timer_daily"))
        sections.append(self.translator.get("commands.help.timer_examples") + "\n")
        
        # Required permissions
        sections.append(f"**{self.translator.get('commands.help.required_permissions')}**")
        sections.append(self.translator.get("commands.help.permissions_for_you"))
        sections.append(self.translator.get("commands.help.permissions_for_bot") + "\n")
        
        # Links
        sections.append(f"**{self.translator.get('commands.help.links')}**")
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
    


class CommandDropdown(discord.ui.Select):
    """Dropdown menu for quick command access"""
    
    def __init__(self, translator, commands_dict):
        self.translator = translator
        self.commands_dict = commands_dict
        
        # Create options from available commands
        options = self.create_options()
        
        if options:  # Only create dropdown if we have options
            super().__init__(
                placeholder=self.translator.get("commands.help.select_command", default="Select a command to learn more..."),
                options=options[:25],  # Discord limit is 25 options
                min_values=1,
                max_values=1
            )
        else:
            # If no options, create a disabled dropdown
            super().__init__(
                placeholder="No commands available",
                options=[discord.SelectOption(label="No commands", value="none")],
                disabled=True
            )
    
    def create_options(self):
        """Create dropdown options from available commands"""
        options = []
        
        # Use the dynamic commands provided
        # Add subscription commands first (most important)
        for cmd in self.commands_dict.get('subscription', [])[:5]:
            emoji = self.get_command_emoji(cmd['name'])
            options.append(
                discord.SelectOption(
                    label=f"/{cmd['name']}",
                    description=cmd['description'][:100],
                    emoji=emoji,
                    value=cmd['name']
                )
            )
        
        # Add general commands
        for cmd in self.commands_dict.get('general', [])[:4]:
            emoji = self.get_command_emoji(cmd['name'])
            options.append(
                discord.SelectOption(
                    label=f"/{cmd['name']}",
                    description=cmd['description'][:100],
                    emoji=emoji,
                    value=cmd['name']
                )
            )
        
        return options
    
    def get_command_emoji(self, cmd_name):
        """Get appropriate emoji for command"""
        emoji_map = {
            "subscription add": "➕",
            "subscription list": "📋",
            "subscription remove": "➖",
            "subscription info": "ℹ️",
            "subscription clear": "🧹",
            "ping": "🏓",
            "help": "❓",
            "timezone change": "🌍",
            "language change": "🌐"
        }
        return emoji_map.get(cmd_name, "▶️")
    
    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        selected_command = self.values[0]
        
        # Create a helpful message about the selected command
        command_details = self.get_command_details(selected_command)
        
        embed = discord.Embed(
            title=f"/{selected_command}",
            description=command_details['description'],
            color=discord.Color.blue()
        )
        
        if command_details.get('usage'):
            embed.add_field(
                name="Usage",
                value=f"`/{command_details['usage']}`",
                inline=False
            )
        
        if command_details.get('examples'):
            embed.add_field(
                name="Examples",
                value="\n".join([f"`{ex}`" for ex in command_details['examples']]),
                inline=False
            )
        
        if command_details.get('permissions'):
            embed.add_field(
                name="Required Permissions",
                value=command_details['permissions'],
                inline=False
            )
        
        embed.set_footer(text="💡 Copy and paste the command to use it!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def get_command_details(self, cmd_name):
        """Get detailed information about a command"""
        command_info = {
            "subscription add": {
                "description": "Subscribe a channel to automatically clear messages based on a timer.",
                "usage": "subscription add <timer> [channel] [target]",
                "examples": [
                    "/subscription add 1h",
                    "/subscription add 30m #general",
                    "/subscription add 08:00,20:00 #announcements"
                ],
                "permissions": "Manage Messages"
            },
            "subscription list": {
                "description": "Display all active subscriptions in the server.",
                "usage": "subscription list",
                "examples": ["/subscription list"],
                "permissions": "None"
            },
            "subscription remove": {
                "description": "Remove an active subscription from a channel.",
                "usage": "subscription remove [channel]",
                "examples": [
                    "/subscription remove",
                    "/subscription remove #general"
                ],
                "permissions": "Manage Messages"
            },
            "subscription info": {
                "description": "View detailed information about a channel's subscription.",
                "usage": "subscription info [channel]",
                "examples": [
                    "/subscription info",
                    "/subscription info #general"
                ],
                "permissions": "None"
            },
            "subscription clear": {
                "description": "Manually trigger a message clear in a subscribed channel.",
                "usage": "subscription clear [channel]",
                "examples": [
                    "/subscription clear",
                    "/subscription clear #general"
                ],
                "permissions": "Manage Messages"
            },
            "ping": {
                "description": "Check the bot's latency and response time.",
                "usage": "ping",
                "examples": ["/ping"],
                "permissions": "None"
            },
            "help": {
                "description": "Display this help message with all available commands.",
                "usage": "help",
                "examples": ["/help"],
                "permissions": "None"
            },
            "timezone change": {
                "description": "Change the default timezone for your server.",
                "usage": "timezone change <timezone>",
                "examples": [
                    "/timezone change America/New_York",
                    "/timezone change Europe/London",
                    "/timezone change EST"
                ],
                "permissions": "Manage Guild"
            },
            "language change": {
                "description": "Change the language for your server.",
                "usage": "language change <language>",
                "examples": [
                    "/language change English",
                    "/language change Danish"
                ],
                "permissions": "Manage Guild"
            }
        }
        
        return command_info.get(cmd_name, {
            "description": "Command information not available.",
            "usage": cmd_name
        })


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