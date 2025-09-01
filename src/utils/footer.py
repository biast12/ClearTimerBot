"""
Footer utility to add a "Powered by" footer to all bot responses
"""


def add_footer(content: str) -> str:
    """
    Add a "Powered by" footer to the content
    
    Args:
        content: The original content
        
    Returns:
        The content with the footer appended
    """
    footer = "\n\n<:logo:1411854240443531384> **Powered by ClearTimer Bot**"
    return content + footer