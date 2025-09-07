"""
Global configuration values with environment variable overrides
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GlobalConfig:
    """Global configuration values that can be overridden via environment variables"""

    # Discord Emoji IDs
    powered_by_emoji_id: str = "1411854240443531384"
    powered_by_emoji_name: str = "logo"

    # Bot Branding
    bot_name: str = "ClearTimerBot"

    # Footer Settings
    show_powered_by_footer: bool = True

    # Cache TTL
    default_cache_ttl_memory: int = 60
    default_cache_ttl_warm: int = 300
    default_cache_ttl_cold: int = 3600

    # Message Settings
    missed_clear_notification_timeout: float = (
        0.0  # Seconds before deleting missed clear notifications (0.0 = never delete)
    )

    # Scheduler Settings
    max_restart_attempts: int = 3
    restart_cooldown: int = 30
    cache_cleanup_interval: int = 900

    # Support Links
    support_server_url: str = "https://biast12.com/botsupport"
    bot_invite_url: str = (
        "https://discord.com/oauth2/authorize?client_id=1290353946308775987&permissions=277025483776&integration_type=0&scope=bot"
    )
    github_url: str = "https://github.com/biast12/ClearTimerBot"

    def __post_init__(self):
        """Load overrides from environment variables"""
        # Discord Emoji IDs
        self.powered_by_emoji_id = os.getenv(
            "POWERED_BY_EMOJI_ID", self.powered_by_emoji_id
        )
        self.powered_by_emoji_name = os.getenv(
            "POWERED_BY_EMOJI_NAME", self.powered_by_emoji_name
        )

        # Bot Branding
        self.bot_name = os.getenv("BOT_NAME", self.bot_name)

        # Footer Settings
        self.show_powered_by_footer = (
            os.getenv("SHOW_POWERED_BY_FOOTER", "true").lower() == "true"
        )

        # Cache TTL
        self.default_cache_ttl_memory = int(
            os.getenv("CACHE_TTL_MEMORY", str(self.default_cache_ttl_memory))
        )
        self.default_cache_ttl_warm = int(
            os.getenv("CACHE_TTL_WARM", str(self.default_cache_ttl_warm))
        )
        self.default_cache_ttl_cold = int(
            os.getenv("CACHE_TTL_COLD", str(self.default_cache_ttl_cold))
        )

        # Message Settings
        self.missed_clear_notification_timeout = float(
            os.getenv(
                "MISSED_CLEAR_NOTIFICATION_TIMEOUT",
                str(self.missed_clear_notification_timeout),
            )
        )

        # Scheduler Settings
        self.max_restart_attempts = int(
            os.getenv("MAX_RESTART_ATTEMPTS", str(self.max_restart_attempts))
        )
        self.restart_cooldown = int(
            os.getenv("RESTART_COOLDOWN", str(self.restart_cooldown))
        )
        self.cache_cleanup_interval = int(
            os.getenv("CACHE_CLEANUP_INTERVAL", str(self.cache_cleanup_interval))
        )

        # Support Links
        self.support_server_url = os.getenv(
            "SUPPORT_SERVER_URL", self.support_server_url
        )
        self.bot_invite_url = os.getenv("BOT_INVITE_URL", self.bot_invite_url)
        self.github_url = os.getenv("GITHUB_URL", self.github_url)


# Singleton instance
_global_config: Optional[GlobalConfig] = None


def get_global_config() -> GlobalConfig:
    """Get or create the global config instance"""
    global _global_config
    if _global_config is None:
        _global_config = GlobalConfig()
    return _global_config


def reload_global_config() -> GlobalConfig:
    """Force reload the global config from environment variables"""
    global _global_config
    _global_config = GlobalConfig()
    return _global_config
