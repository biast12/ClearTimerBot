"""
View Display for Error Handling
"""

import discord
from typing import Optional


class ErrorView(discord.ui.LayoutView):
    """View for error messages"""
    
    def __init__(self, title: str, description: str, error_id: Optional[str] = None):
        super().__init__()
        
        content = f"{title}\n\n{description}"
        
        if error_id:
            content += f"\n\nError ID: `{error_id}`"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class MissedClearView(discord.ui.LayoutView):
    """View for missed clear notification"""
    
    def __init__(self):
        super().__init__()
        
        content = (
            "⚠️ **Missed Clear Notification**\n\n"
            "A scheduled message clear was missed for this channel.\n"
            "The timer has been rescheduled."
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)