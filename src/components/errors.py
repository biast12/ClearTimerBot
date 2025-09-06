"""
View Display for Error Handling
"""

import discord
from typing import Optional
from src.utils.footer import add_footer


class ErrorView(discord.ui.LayoutView):
    """View for error messages"""
    
    def __init__(self, title: str, description: str, error_id: Optional[str] = None):
        super().__init__()
        
        content = f"{title}\n\n{description}"
        
        if error_id:
            content += f"\n\nError ID: `{error_id}`"
        
        content = add_footer(content, translator)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class MissedClearView(discord.ui.LayoutView):
    """View for missed clear notification"""
    
    def __init__(self, translator):
        super().__init__()
        
        content = add_footer(translator.get("errors.missed_clear_notification", translator))
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)