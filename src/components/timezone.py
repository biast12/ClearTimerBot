"""
View Display for Timezone Commands
"""

import discord
from datetime import datetime
import pytz
from typing import Optional, Dict
from src.utils.footer import add_footer


class TimezoneChangeSuccessView(discord.ui.LayoutView):
    """View for successful timezone change"""

    def __init__(self, timezone: str, translator):
        super().__init__()

        message = translator.get("commands.timezone.change.success", timezone=timezone)
        content = add_footer(message, translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class TimezoneListView(discord.ui.LayoutView):
    """View for listing available timezones from config"""

    def __init__(self, timezones_dict: Dict[str, str], translator):
        super().__init__()

        lines = []
        lines.append(f"**{translator.get('commands.timezone.list.title')}**\n")
        lines.append(translator.get("commands.timezone.list.description") + "\n")

        if not timezones_dict:
            content = add_footer(
                "🌍 **Available Timezones**\n\n"
                "No timezones configured in the database.\n\n"
                "**Common timezone examples:**\n"
                "`America/New_York` - Eastern Time\n"
                "`America/Los_Angeles` - Pacific Time\n"
                "`Europe/London` - British Time\n"
                "`Asia/Tokyo` - Japan Time\n"
                "`Australia/Sydney` - Sydney Time\n\n"
                "Use `/timezone change <timezone>` with any valid timezone.",
                translator,
            )
        else:
            # Format timezone list
            for abbr, full_name in sorted(timezones_dict.items()):
                lines.append(f"**{abbr}**: {full_name}")

            content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class TimezoneInvalidView(discord.ui.LayoutView):
    """View for invalid timezone input"""

    def __init__(self, timezone: str, suggestion: Optional[str], translator):
        super().__init__()

        lines = []
        lines.append(
            translator.get("commands.timezone.change.invalid", timezone=timezone)
        )

        if suggestion:
            lines.append("")
            lines.append(
                translator.get(
                    "commands.timezone.change.suggestion", suggestion=suggestion
                )
            )

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)
