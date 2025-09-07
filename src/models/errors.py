from enum import Enum


class LogArea(Enum):
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"
    DATABASE = "DATABASE"
    DISCORD = "DISCORD"
    COMMANDS = "COMMANDS"
    SCHEDULER = "SCHEDULER"
    CACHE = "CACHE"
    CLEANUP = "CLEANUP"
    ERROR = "ERROR"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    PERMISSIONS = "PERMISSIONS"
    GENERAL = "GENERAL"
    NONE = "NONE"  # Special case - doesn't display area field
