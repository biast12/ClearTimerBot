"""
Discord command localization utilities
Provides localized names and descriptions for Discord command registration
"""

from typing import Dict, Optional
import discord
from src.utils.logger import logger, LogArea

# Map our language codes to Discord locale codes
LANGUAGE_TO_DISCORD_LOCALE = {
    "da": discord.Locale.danish,  # Danish
    "de": discord.Locale.german,  # German
    "es": discord.Locale.spain_spanish,  # Spanish
    "zh": discord.Locale.chinese,  # Chinese (Simplified)
    "hi": discord.Locale.hindi,  # Hindi
    # Note: Arabic and Bengali are not directly supported by Discord
    # We'll keep them in our internal localization but not for Discord commands
}


def get_command_description(command_key: str, lang_code: str = None) -> str:
    """
    Get a command description with automatic fallback to English

    Args:
        command_key: The command key (e.g., "help", "subscription.add")
        lang_code: The language code (defaults to English)

    Returns:
        The localized command description, or English if not found
    """
    # Import here to avoid circular dependency
    from src.localization import get_i18n

    i18n = get_i18n()

    if lang_code is None:
        lang_code = i18n.default_language

    # Build the full key path
    key_parts = command_key.split(".")
    if len(key_parts) == 1:
        # Top-level command like "help" or "ping"
        full_key = f"commands.{command_key}.description"
    elif len(key_parts) == 2:
        # Subcommand like "subscription.add"
        full_key = f"commands.{key_parts[0]}.{key_parts[1]}.description"
    else:
        # Nested subcommand like "admin.blacklist.add"
        full_key = f"commands.{'.'.join(key_parts)}.description"

    # Try to get the description in the requested language
    description = i18n._get_nested_value(i18n.languages.get(lang_code, {}), full_key)

    # Fallback to English if not found
    if description is None and lang_code != i18n.default_language:
        description = i18n._get_nested_value(
            i18n.languages.get(i18n.default_language, {}), full_key
        )

    # If still not found, return a default message
    if description is None:
        logger.warning(
            LogArea.GENERAL,
            f"Command description not found for '{command_key}' in any language",
        )
        return f"Command: {command_key}"

    return description


def get_localized_descriptions(command_key: str) -> Dict[discord.Locale, str]:
    """
    Get localized descriptions for a command in all supported languages

    Args:
        command_key: The command key (e.g., "help", "subscription.add")

    Returns:
        Dictionary mapping Discord locales to localized descriptions
    """
    from src.localization import get_i18n

    i18n = get_i18n()
    localizations = {}

    for lang_code, discord_locale in LANGUAGE_TO_DISCORD_LOCALE.items():
        if not i18n.is_language_supported(lang_code):
            continue

        # Get the description in this language using the local function
        description = get_command_description(command_key, lang_code)

        # Only add if we got a valid description (not the missing key message)
        if (
            description
            and not description.startswith("[MISSING:")
            and not description.startswith("Command:")
        ):
            localizations[discord_locale] = description

    return localizations


def get_localized_names(
    name: str, translations: Optional[Dict[str, str]] = None
) -> Dict[discord.Locale, str]:
    """
    Get localized names for a command
    Currently returns empty dict as we keep command names in English
    But this can be expanded if we want to localize command names too

    Args:
        name: The command name
        translations: Optional dictionary of translations

    Returns:
        Dictionary mapping Discord locales to localized names
    """
    # For now, we keep command names in English for consistency
    # But this function is here if we want to localize names in the future
    return {}


def apply_localizations(command_decorator):
    """
    Decorator to automatically apply localizations to a command
    This is a helper function to make it easier to add localizations
    """

    def wrapper(func):
        # The actual decoration happens in the command files
        return command_decorator(func)

    return wrapper


# Pre-load all command description localizations for efficiency
_COMMAND_LOCALIZATIONS_CACHE = {}


def get_command_localizations(command_key: str) -> Dict[str, Dict[discord.Locale, str]]:
    """
    Get both name and description localizations for a command

    Args:
        command_key: The command key (e.g., "help", "subscription.add")

    Returns:
        Dictionary with 'names' and 'descriptions' keys containing localizations
    """
    if command_key not in _COMMAND_LOCALIZATIONS_CACHE:
        _COMMAND_LOCALIZATIONS_CACHE[command_key] = {
            "names": get_localized_names(command_key),
            "descriptions": get_localized_descriptions(command_key),
        }

    return _COMMAND_LOCALIZATIONS_CACHE[command_key]


def clear_cache():
    """Clear the localizations cache (useful for reloading)"""
    global _COMMAND_LOCALIZATIONS_CACHE
    _COMMAND_LOCALIZATIONS_CACHE = {}
