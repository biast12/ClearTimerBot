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
    
    def __init__(self, timezone: str, auto_detected: bool = False):
        super().__init__()
        
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            offset = now.strftime("%z")
            formatted_offset = f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"
            current_time = now.strftime("%I:%M %p")
            
            detection_method = "🔍 **Auto-Detected**\n\n" if auto_detected else ""
            
            content = add_footer(
                f"✅ **Timezone Updated**\n\n"
                f"{detection_method}"
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


class TimezoneListView(discord.ui.LayoutView):
    """View for listing available timezones from config"""
    
    def __init__(self, timezones_dict: Dict[str, str]):
        super().__init__()
        
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
            # Group timezones by region
            regions = {}
            for abbr, tz in sorted(timezones_dict.items()):
                # Get region from timezone (e.g., America from America/New_York)
                if '/' in tz:
                    region = tz.split('/')[0]
                else:
                    region = "Other"
                
                if region not in regions:
                    regions[region] = []
                regions[region].append(f"`{abbr}` → {tz}")
            
            content_parts = ["🌍 **Available Timezones**\n"]
            
            # Sort regions and display
            for region in sorted(regions.keys()):
                if region == "America":
                    emoji = "🌎"
                elif region == "Europe":
                    emoji = "🇪🇺"
                elif region == "Asia":
                    emoji = "🌏"
                elif region == "Australia":
                    emoji = "🇦🇺"
                elif region == "Pacific":
                    emoji = "🏝️"
                else:
                    emoji = "🌐"
                    
                content_parts.append(f"\n**{emoji} {region}**")
                for tz_entry in regions[region][:10]:  # Limit to 10 per region
                    content_parts.append(tz_entry)
                if len(regions[region]) > 10:
                    content_parts.append(f"*...and {len(regions[region]) - 10} more*")
            
            content_parts.append("\n**Usage**")
            content_parts.append("Use `/timezone change <timezone>` with any of these values.")
            content_parts.append("You can use either the abbreviation (e.g., `EST`) or full name (e.g., `America/New_York`).")
            
            content = add_footer("\n".join(content_parts))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
        )
        self.add_item(container)


class InvalidTimezoneView(discord.ui.LayoutView):
    """View for invalid timezone error"""
    
    def __init__(self, timezone_input: str, suggestion: Optional[str] = None):
        super().__init__()
        
        suggestion_text = ""
        if suggestion:
            suggestion_text = f"\n**Did you mean?** `{suggestion}`\n"
        
        content = add_footer(
            f"❌ **Invalid Timezone**\n\n"
            f"The timezone `{timezone_input}` is not recognized.\n"
            f"{suggestion_text}\n"
            f"**Examples of valid timezones:**\n"
            f"`America/New_York` - Eastern Time\n"
            f"`Europe/London` - British Time\n"
            f"`Asia/Tokyo` - Japan Time\n"
            f"`Australia/Sydney` - Sydney Time\n\n"
            f"**💡 Tips**\n"
            f"• Use `/timezone list` to see available timezones\n"
            f"• Timezones are case-sensitive\n"
            f"• Use the full timezone name (e.g., `America/New_York`)"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
        )
        self.add_item(container)


class CurrentTimezoneView(discord.ui.LayoutView):
    """View for displaying current timezone"""
    
    def __init__(self, timezone: Optional[str], auto_detected: bool = False):
        super().__init__()
        
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)
                offset = now.strftime("%z")
                formatted_offset = f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"
                current_time = now.strftime("%I:%M %p on %B %d, %Y")
                
                detection_method = " (Auto-detected)" if auto_detected else " (Manually set)"
                
                content = add_footer(
                    f"🌍 **Current Server Timezone**\n\n"
                    f"**Timezone:** `{timezone}`{detection_method}\n"
                    f"**Offset:** {formatted_offset}\n"
                    f"**Current Time:** {current_time}\n\n"
                    f"**This means:**\n"
                    f"• Users can set timers with just time: `/subscription add 21:30`\n"
                    f"• The server timezone will be used automatically\n"
                    f"• Users can still override: `/subscription add 21:30 PST`\n\n"
                    f"To change the timezone, use `/timezone change <timezone>`"
                )
            except Exception:
                content = add_footer(
                    f"🌍 **Current Server Timezone**\n\n"
                    f"**Timezone:** `{timezone}`\n"
                    f"**Error:** Could not load timezone details\n\n"
                    f"To change the timezone, use `/timezone change <timezone>`"
                )
        else:
            content = add_footer(
                "❌ **No Timezone Set**\n\n"
                "This server doesn't have a default timezone configured.\n"
                "When users create timers without specifying a timezone, UTC will be used.\n\n"
                "**Set a timezone to:**\n"
                "• Simplify timer creation - users can just specify time (e.g., `21:30`)\n"
                "• Avoid confusion with timezone abbreviations\n"
                "• Make scheduling easier for users in the same region\n\n"
                "Use `/timezone change <timezone>` to set a default timezone.\n"
                "Use `/timezone list` to see available timezones."
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
        )
        self.add_item(container)