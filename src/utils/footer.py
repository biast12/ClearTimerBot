"""
Footer utility to add a "Powered by" footer to all bot responses
"""

from typing import Optional
from src.config import get_global_config


def add_footer(content: str, translator: Optional[object] = None) -> str:
    """
    Add a "Powered by" footer to the content
    
    Args:
        content: The original content
        translator: Optional translator instance for localized footer text
        
    Returns:
        The content with the footer appended
    """
    config = get_global_config()
    
    if not config.show_powered_by_footer:
        return content
    
    emoji = f"<:{config.powered_by_emoji_name}:{config.powered_by_emoji_id}> " if config.powered_by_emoji_id else ""
    text = translator.get("components.powered_by", bot_name=config.bot_name)
    
    footer = f"\n\n{emoji}{text}"
    return content + footer