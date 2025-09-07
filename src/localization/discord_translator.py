"""
Discord.py Translator implementation for command localizations
Uses our existing i18n system to provide translations for Discord commands
"""

from typing import Optional
import discord
from discord import app_commands
from src.localization import get_i18n
from src.localization.discord_localizations import get_command_description


class ClearTimerTranslator(app_commands.Translator):
    """Custom translator that uses our i18n system for Discord command localizations"""

    def __init__(self):
        super().__init__()
        self.i18n = get_i18n()

        # Map Discord locales to our language codes
        self.locale_map = {
            discord.Locale.danish: "da",
            discord.Locale.german: "de",
            discord.Locale.spain_spanish: "es",
            discord.Locale.chinese: "zh",
            discord.Locale.hindi: "hi",
        }

    async def load(self) -> None:
        """Setup function called when translator is set"""
        # Ensure i18n is loaded
        if not hasattr(self.i18n, "_translations") or not self.i18n._translations:
            self.i18n.load_languages()

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> Optional[str]:
        """
        Translate a string to the specified locale

        Args:
            string: The string being translated
            locale: The locale being requested for translation
            context: The translation context (command, parameter, etc.)

        Returns:
            The translated string or None if no translation available
        """
        # Get our language code from Discord locale
        lang_code = self.locale_map.get(locale)
        if not lang_code:
            return None

        # Check if we support this language
        if not self.i18n.is_language_supported(lang_code):
            return None

        # Get the message to translate
        message = str(string)

        # We only translate descriptions, not command names
        # Return None for command/group names to keep them in English
        if context.type in [
            app_commands.TranslationContextType.command_name,
            app_commands.TranslationContextType.group_name,
        ]:
            return None

        # For command descriptions, we need to look them up
        # Context provides information about where this string is from
        if context.type == app_commands.TranslationContextType.command_description:
            # Build command key from the command structure
            if context.data.parent:
                # It's a subcommand or group command
                parent_name = context.data.parent.name
                command_name = context.data.name
                command_key = f"{parent_name}.{command_name}"
            else:
                # It's a top-level command
                command_key = context.data.name

            # Get the translated description
            description = get_command_description(command_key, lang_code)

            # Only return if we got a valid translation (not the fallback)
            if (
                description
                and not description.startswith("[MISSING:")
                and not description.startswith("Command:")
            ):
                # Also check it's different from the original
                english_desc = get_command_description(command_key, "en")
                if description != english_desc or lang_code != "en":
                    return description

        elif context.type == app_commands.TranslationContextType.group_description:
            # For group descriptions
            group_key = context.data.name
            description = get_command_description(group_key, lang_code)

            if (
                description
                and not description.startswith("[MISSING:")
                and not description.startswith("Command:")
            ):
                english_desc = get_command_description(group_key, "en")
                if description != english_desc or lang_code != "en":
                    return description

        # Return None if no translation found
        return None
