"""
Footer utility to add a "Powered by" footer to all bot responses
"""

from src.config import get_global_config


def add_footer(content: str) -> str:
    """
    Add a "Powered by" footer to the content
    
    Args:
        content: The original content
        
    Returns:
        The content with the footer appended
    """
    config = get_global_config()
    footer = config.get_footer_text()
    return content + footer if footer else content