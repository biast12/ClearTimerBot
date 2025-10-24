import json
import re
from typing import Dict, Any, Optional
from pathlib import Path
import discord
from src.utils.logger import logger, LogArea


class I18n:
    """Internationalization manager for the bot"""

    def __init__(self):
        self.languages: Dict[str, Dict[str, Any]] = {}
        self.default_language = "en"
        self.language_names: Dict[str, str] = {}
        self.load_languages()

    def load_languages(self) -> None:
        """Load all language files from the languages directory"""
        languages_dir = Path(__file__).parent / "languages"
        languages_dir.mkdir(exist_ok=True)

        for lang_file in languages_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    lang_data = json.load(f)
                    self.languages[lang_code] = lang_data
                    self.language_names[lang_code] = lang_data.get(
                        "language_name", lang_code
                    )
            except Exception as e:
                logger.error(
                    LogArea.STARTUP, f"Failed to load language file {lang_file}: {e}"
                )

    def get_available_languages(self) -> Dict[str, str]:
        """Get all available languages with their display names"""
        return self.language_names.copy()

    def is_language_supported(self, lang_code: str) -> bool:
        """Check if a language is supported"""
        return lang_code in self.languages

    def get(self, key: str, lang_code: str = None, **kwargs) -> str:
        """
        Get a translated string with fallback mechanism

        Args:
            key: The translation key (e.g., "commands.ping.response")
            lang_code: The language code to use (defaults to English)
            **kwargs: Variables to format in the string

        Returns:
            The translated string, or the key itself if not found
        """
        if lang_code is None:
            lang_code = self.default_language

        # Try to get from requested language
        text = self._get_nested_value(self.languages.get(lang_code, {}), key)

        # Fallback to English if not found
        if text is None and lang_code != self.default_language:
            text = self._get_nested_value(
                self.languages.get(self.default_language, {}), key
            )
            if text is not None:
                logger.warning(
                    LogArea.GENERAL,
                    f"Translation key '{key}' not found in language '{lang_code}', falling back to English",
                )

        # If still not found, return the key itself
        if text is None:
            logger.error(
                LogArea.GENERAL,
                f"Translation key not found: '{key}' (requested language: '{lang_code}'). "
                f"This key doesn't exist in any language file.",
            )
            return f"[MISSING: {key}]"  # Make it obvious in the UI that a translation is missing

        # Format the string with provided variables
        try:
            formatted = text.format(**kwargs) if kwargs else text
            return formatted
        except KeyError as e:
            missing_param = str(e).strip("'")
            logger.error(
                LogArea.GENERAL,
                f"Missing parameter '{missing_param}' when formatting translation key '{key}'. "
                f"Expected parameters: {self._extract_parameters(text)}, "
                f"Provided parameters: {list(kwargs.keys())}",
            )
            return text
        except Exception as e:
            logger.error(
                LogArea.GENERAL, f"Error formatting translation key '{key}': {e}"
            )
            return text

    def _extract_parameters(self, text: str) -> list:
        """Extract parameter names from a format string"""
        # Find all {param} style parameters
        params = re.findall(r"\{([^}]+)\}", text)
        # Filter out format specifiers and special syntax
        return [p for p in params if ":" not in p and "," not in p and " " not in p]

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """Get a value from nested dictionary using dot notation"""
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current if isinstance(current, str) else None

    def detect_server_language(self, guild: discord.Guild) -> str:
        """
        Detect the preferred language for a Discord server

        Args:
            guild: The Discord guild object

        Returns:
            The detected language code, or default if detection fails
        """
        # Map Discord locales to our language codes
        locale_mapping = {
            "en-US": "en",
            "en-GB": "en",
            "da": "da",
            "da-DK": "da",
            "de": "de",
            "de-DE": "de",
            "es-ES": "es",
            "es-419": "es",
            "zh-CN": "zh",
            "zh-TW": "zh",
            "hi": "hi",
            "ar": "ar",
            "bn": "bn",
        }

        # Try to use guild's preferred locale
        if hasattr(guild, "preferred_locale") and guild.preferred_locale:
            locale_str = str(guild.preferred_locale)
            # Check direct match
            if locale_str in locale_mapping:
                lang_code = locale_mapping[locale_str]
                if self.is_language_supported(lang_code):
                    return lang_code
            # Check language code only (e.g., "da" from "da-DK")
            lang_prefix = locale_str.split("-")[0]
            if self.is_language_supported(lang_prefix):
                return lang_prefix

        return self.default_language


class Translator:
    """Context-aware translator for a specific guild"""

    def __init__(self, i18n: I18n, lang_code: str):
        self.i18n = i18n
        self.lang_code = lang_code

    def get(self, key: str, **kwargs) -> str:
        """Get a translated string for this translator's language"""
        return self.i18n.get(key, self.lang_code, **kwargs)


# Global I18n instance
_i18n = I18n()


async def get_translator(guild_id: str, data_service) -> Translator:
    """
    Get a translator for a specific guild

    Args:
        guild_id: The guild ID
        data_service: The data service to get server preferences

    Returns:
        A Translator instance for the guild's language
    """
    # Get the server's language preference
    language = await data_service.get_server_language(guild_id)

    # Use default if no language is set or if language is not supported
    if not language or not _i18n.is_language_supported(language):
        language = _i18n.default_language

    return Translator(_i18n, language)


def get_i18n() -> I18n:
    """Get the global I18n instance"""
    return _i18n
