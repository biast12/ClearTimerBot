"""
View Display for Timezone Commands
"""

import discord
from datetime import datetime
import pytz
from typing import Optional, Dict
from src.utils.footer import add_footer


class TimezoneChangeView(discord.ui.LayoutView):
    """View for successful timezone change"""
    
    def __init__(self, timezone: str, translator):
        super().__init__()
        
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            offset = now.strftime("%z")
            formatted_offset = f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"
            current_time = now.strftime("%I:%M %p")
            
            content = add_footer(
                f"✅ **Timezone Updated**\n\n"
                f"**Timezone:** `{timezone}`\n"
                f"**Offset:** {formatted_offset}\n"
                f"**Current Time:** {current_time}\n\n"
                f"**How it works:**\n"
                f"• When users specify times without a timezone (e.g., `21:30`), this timezone will be used\n"
                f"• Users can still override by specifying a timezone (e.g., `21:30 EST`)\n"
                f"• To change it again, use `/timezone change`"
            )
        except Exception:
            content = add_footer(
                f"✅ **Timezone Updated**\n\n"
                f"**Timezone:** `{timezone}`"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
        )
        self.add_item(container)


class TimezoneChangeSuccessView(discord.ui.LayoutView):
    """View for successful timezone change"""
    
    def __init__(self, timezone: str, translator):
        super().__init__()
        
        message = translator.get("commands.timezone.change.success", timezone=timezone)
        content = add_footer(message)
        
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
                "Use `/timezone change <timezone>` with any valid timezone."
            )
        else:
            # Format timezone list
            for abbr, full_name in sorted(timezones_dict.items()):
                lines.append(f"**{abbr}**: {full_name}")
            
            content = add_footer("\n".join(lines))
        
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
        lines.append(translator.get("commands.timezone.change.invalid", timezone=timezone))
        
        if suggestion:
            lines.append("")
            lines.append(translator.get("commands.timezone.change.suggestion", suggestion=suggestion))
        
        content = add_footer("\n".join(lines))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class InvalidTimezoneView(discord.ui.LayoutView):
    """View for invalid timezone error"""
    
    def __init__(self, timezone_input: str, suggestion: Optional[str], translator):
        super().__init__()
        
        lines = []
        lines.append(translator.get("commands.timezone.change.invalid", timezone=timezone_input))
            
        if suggestion:
            lines.append("")
            lines.append(translator.get("commands.timezone.change.suggestion", suggestion=suggestion))
        
        content = add_footer("\n".join(lines))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class CurrentTimezoneView(discord.ui.LayoutView):
    """View for displaying current timezone"""
    
    def __init__(self, timezone: Optional[str], translator):
        super().__init__()
        
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)
                offset = now.strftime("%z")
                formatted_offset = f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"
                current_time = now.strftime("%I:%M %p on %B %d, %Y")
                
                status_msg = translator.get("commands.timezone.current.timezone", timezone=timezone)
                
                lines = [
                    f"🌍 **{translator.get('commands.timezone.current.title')}**\n",
                    status_msg,
                    translator.get("commands.timezone.current.offset", offset=formatted_offset),
                    translator.get("commands.timezone.current.time", time=current_time),
                    "",
                    f"**{translator.get('commands.timezone.current.how_it_works')}**",
                    translator.get("commands.timezone.current.benefit_1"),
                    translator.get("commands.timezone.current.benefit_2"),
                    translator.get("commands.timezone.current.benefit_3"),
                    "",
                    translator.get("commands.timezone.current.change_hint")
                ]
                content = add_footer("\n".join(lines))
            except Exception:
                lines = [
                    f"🌍 **{translator.get('commands.timezone.current.title')}**\n",
                    translator.get("commands.timezone.current.timezone", timezone=timezone),
                    translator.get("commands.timezone.current.error"),
                    "",
                    translator.get("commands.timezone.current.change_hint")
                ]
                content = add_footer("\n".join(lines))
        else:
            lines = [
                f"❌ **{translator.get('commands.timezone.current.no_timezone_title')}**\n",
                translator.get("commands.timezone.current.no_timezone_description"),
                "",
                f"**{translator.get('commands.timezone.current.set_timezone_benefits')}**",
                translator.get("commands.timezone.current.benefit_1"),
                translator.get("commands.timezone.current.benefit_2"),
                translator.get("commands.timezone.current.benefit_3"),
                "",
                translator.get("commands.timezone.current.set_hint"),
                translator.get("commands.timezone.current.list_hint")
            ]
            content = add_footer("\n".join(lines))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value if timezone else discord.Color.orange().value,
        )
        self.add_item(container)