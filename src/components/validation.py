"""
View Display for Validation Errors
"""

import discord
from src.utils.footer import add_footer


class ValidationErrorView(discord.ui.LayoutView):
    """View for validation error messages"""

    def __init__(self, error_message: str, translator):
        super().__init__()

        # Parse the error message to determine type
        if (
            "validation.blacklisted" in error_message
            or "blacklisted" in error_message.lower()
        ):
            title = translator.get("validation.error_titles.blacklisted")
            color = discord.Color.red()
        elif "validation.insufficient_permissions" in error_message or (
            "permission" in error_message.lower() and "need" in error_message.lower()
        ):
            title = translator.get("validation.error_titles.insufficient_permissions")
            color = discord.Color.orange()
        elif (
            "validation.bot_missing_permissions" in error_message
            or "missing the following permissions" in error_message
        ):
            title = translator.get("validation.error_titles.bot_missing_permissions")
            color = discord.Color.orange()
        elif (
            "validation.not_subscribed" in error_message
            or "not subscribed" in error_message
        ):
            title = "Channel Not Subscribed"
            color = discord.Color.yellow()
        elif (
            "validation.channel_already_subscribed" in error_message
            or "already has a timer" in error_message
        ):
            title = translator.get("validation.error_titles.channel_already_subscribed")
            color = discord.Color.yellow()
        else:
            title = translator.get("validation.error_titles.general")
            color = discord.Color.red()

        # Clean up the message for better formatting
        clean_message = error_message.replace("❌ ", "")

        content = add_footer(f"❌ **{title}**\n\n{clean_message}", translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content), accent_color=color.value
        )
        self.add_item(container)
