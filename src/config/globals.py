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
    bot_color: int = 0x5865F2  # Discord Blurple
    error_color: int = 0xED4245  # Discord Red
    success_color: int = 0x57F287  # Discord Green
    warning_color: int = 0xFEE75C  # Discord Yellow
    
    # Footer Settings
    show_powered_by_footer: bool = True
    
    # Rate Limiting
    max_clears_per_minute: int = 5
    max_subscriptions_per_server: int = 50
    
    # Cache TTL (in seconds)
    default_cache_ttl_memory: int = 60  # 1 minute
    default_cache_ttl_warm: int = 300  # 5 minutes
    default_cache_ttl_cold: int = 3600  # 1 hour
    
    # Message Settings
    ephemeral_error_timeout: float = 10.0  # Delete error messages after 10 seconds
    missed_clear_notification_timeout: float = 60.0  # Delete missed clear notifications after 60 seconds
    
    # Scheduler Settings
    max_restart_attempts: int = 3
    restart_cooldown: int = 30  # seconds
    cache_cleanup_interval: int = 900  # 15 minutes
    
    # Database Settings
    removed_servers_retention_days: int = 30
    error_logs_retention_days: int = 7
    
    # Support Links
    support_server_url: str = "https://biast12.com/botsupport"
    terms_of_service_url: str = "https://biast12.com/cleartimer/termsofservice"
    privacy_policy_url: str = "https://biast12.com/cleartimer/privacypolicy"
    bot_invite_url: str = "https://discord.com/oauth2/authorize?client_id=1290353946308775987&permissions=277025483776&integration_type=0&scope=bot"
    github_url: str = "https://github.com/biast12/ClearTimerBot"
    
    def __post_init__(self):
        """Load overrides from environment variables"""
        # Discord Emoji IDs
        self.powered_by_emoji_id = os.getenv("POWERED_BY_EMOJI_ID", self.powered_by_emoji_id)
        self.powered_by_emoji_name = os.getenv("POWERED_BY_EMOJI_NAME", self.powered_by_emoji_name)
        
        # Bot Branding
        self.bot_name = os.getenv("BOT_NAME", self.bot_name)
        self.bot_color = int(os.getenv("BOT_COLOR", str(self.bot_color)), 16) if os.getenv("BOT_COLOR") else self.bot_color
        self.error_color = int(os.getenv("ERROR_COLOR", str(self.error_color)), 16) if os.getenv("ERROR_COLOR") else self.error_color
        self.success_color = int(os.getenv("SUCCESS_COLOR", str(self.success_color)), 16) if os.getenv("SUCCESS_COLOR") else self.success_color
        self.warning_color = int(os.getenv("WARNING_COLOR", str(self.warning_color)), 16) if os.getenv("WARNING_COLOR") else self.warning_color
        
        # Footer Settings
        self.show_powered_by_footer = os.getenv("SHOW_POWERED_BY_FOOTER", "true").lower() == "true"
        
        # Rate Limiting
        self.max_clears_per_minute = int(os.getenv("MAX_CLEARS_PER_MINUTE", str(self.max_clears_per_minute)))
        self.max_subscriptions_per_server = int(os.getenv("MAX_SUBSCRIPTIONS_PER_SERVER", str(self.max_subscriptions_per_server)))
        
        # Cache TTL
        self.default_cache_ttl_memory = int(os.getenv("CACHE_TTL_MEMORY", str(self.default_cache_ttl_memory)))
        self.default_cache_ttl_warm = int(os.getenv("CACHE_TTL_WARM", str(self.default_cache_ttl_warm)))
        self.default_cache_ttl_cold = int(os.getenv("CACHE_TTL_COLD", str(self.default_cache_ttl_cold)))
        
        # Message Settings
        self.ephemeral_error_timeout = float(os.getenv("EPHEMERAL_ERROR_TIMEOUT", str(self.ephemeral_error_timeout)))
        self.missed_clear_notification_timeout = float(os.getenv("MISSED_CLEAR_NOTIFICATION_TIMEOUT", str(self.missed_clear_notification_timeout)))
        
        # Scheduler Settings
        self.max_restart_attempts = int(os.getenv("MAX_RESTART_ATTEMPTS", str(self.max_restart_attempts)))
        self.restart_cooldown = int(os.getenv("RESTART_COOLDOWN", str(self.restart_cooldown)))
        self.cache_cleanup_interval = int(os.getenv("CACHE_CLEANUP_INTERVAL", str(self.cache_cleanup_interval)))
        
        # Database Settings
        self.removed_servers_retention_days = int(os.getenv("REMOVED_SERVERS_RETENTION_DAYS", str(self.removed_servers_retention_days)))
        self.error_logs_retention_days = int(os.getenv("ERROR_LOGS_RETENTION_DAYS", str(self.error_logs_retention_days)))
        
        # Support Links
        self.support_server_url = os.getenv("SUPPORT_SERVER_URL", self.support_server_url)
        self.terms_of_service_url = os.getenv("TERMS_OF_SERVICE_URL", self.terms_of_service_url)
        self.privacy_policy_url = os.getenv("PRIVACY_POLICY_URL", self.privacy_policy_url)
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